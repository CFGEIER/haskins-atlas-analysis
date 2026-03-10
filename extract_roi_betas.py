#!/usr/bin/env python3
"""
Extract mean beta/signal values from HaskinsPeds atlas ROIs using nilearn.
Outputs a CSV with region_id, region_name, and mean_beta for each atlas region.
"""

import os
import sys

# Add script directory for config import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DATA_DIR, OUTPUT_DIR, HASKINS_ATLAS, GROUP_MAP

import numpy as np
import nibabel as nib
from nibabel.nifti1 import Nifti1Image
from nilearn.image import check_niimg, resample_img
from nilearn.maskers import NiftiLabelsMasker
import pandas as pd


def load_label_lut(atlas_path):
    """
    Load label ID -> region name mapping. Uses HaskinsAtlas_LUT.txt for Haskins
    atlas (correct mapping); otherwise FreeSurfer LUT.
    """
    atlas_basename = os.path.basename(str(atlas_path)).lower()
    if "haskins" in atlas_basename:
        # Haskins atlas has its own label scheme (not FreeSurfer)
        candidates = [
            os.path.join(os.path.dirname(__file__), "HaskinsAtlas_LUT.txt"),
            os.path.join(DATA_DIR, "HaskinsAtlas_LUT.txt"),
        ]
        for p in candidates:
            if os.path.exists(p):
                try:
                    lut = {}
                    with open(p) as f:
                        for line in f:
                            line = line.strip()
                            if not line or line.startswith("#"):
                                continue
                            parts = line.split(None, 1)
                            if len(parts) >= 2:
                                try:
                                    lut[int(parts[0])] = parts[1]
                                except ValueError:
                                    continue
                    return lut
                except Exception as e:
                    print(f"Warning: Could not load Haskins LUT ({e}). Using region_id only.")
                    return {}
        print("Warning: HaskinsAtlas_LUT.txt not found. Using region_id only.")
        return {}

    # FreeSurfer LUT for non-Haskins atlases
    lut_url = "https://raw.githubusercontent.com/freesurfer/freesurfer/dev/distribution/FreeSurferColorLUT.txt"
    candidates = [
        os.path.join(os.path.dirname(__file__), "FreeSurferColorLUT.txt"),
        os.path.join(DATA_DIR, "FreeSurferColorLUT.txt"),
    ]
    if os.environ.get("FREESURFER_HOME"):
        candidates.append(os.path.join(os.environ["FREESURFER_HOME"], "FreeSurferColorLUT.txt"))
    path = None
    for p in candidates:
        if os.path.exists(p):
            path = p
            break
    if path is None:
        path = lut_url
    try:
        if path.startswith("http"):
            import urllib.request
            with urllib.request.urlopen(path) as f:
                lines = f.read().decode().splitlines()
        else:
            with open(path) as f:
                lines = f.readlines()
        lut = {}
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                try:
                    idx = int(parts[0])
                    lut[idx] = parts[1]
                except ValueError:
                    continue
        return lut
    except Exception as e:
        print(f"Warning: Could not load FreeSurfer LUT ({e}). Using region_id only.")
        return {}


def extract_thresholded_means(
    data_3d, atlas_img, threshold, cluster_size=None, background_label=0, per_cluster=False
):
    """
    Extract mean of voxels exceeding threshold per ROI.
    If cluster_size is set, only voxels in clusters of at least that many voxels
    (26-connectivity) are included.
    If per_cluster=True and cluster_size is set, returns one entry per cluster per ROI
    (cluster_rank 1 = largest cluster in that ROI).
    Returns:
      - per_cluster=False: (region_ids, means)
      - per_cluster=True: list of (region_id, cluster_rank, n_voxels, mean)
    """
    from scipy import ndimage
    from nilearn._utils.niimg import safe_get_data

    data_img = check_niimg(data_3d, atleast_4d=True)
    atlas_resampled = resample_img(
        atlas_img,
        interpolation="nearest",
        target_shape=data_img.shape[:3],
        target_affine=data_img.affine,
    )
    data_arr = np.asarray(safe_get_data(data_img, ensure_finite=True)).squeeze()
    labels_arr = np.asarray(safe_get_data(atlas_resampled)).astype(int)

    above_threshold = data_arr > threshold
    if cluster_size is not None and cluster_size > 0:
        structure = np.ones((3, 3, 3))
        cluster_labels, n_clusters = ndimage.label(above_threshold, structure=structure)
        cluster_sizes = np.bincount(cluster_labels.ravel())[1:]  # exclude 0
        large_cluster_ids = np.where(cluster_sizes >= cluster_size)[0] + 1
        in_large_cluster = np.isin(cluster_labels, large_cluster_ids)
        voxel_mask = above_threshold & in_large_cluster
    else:
        cluster_labels = None
        voxel_mask = above_threshold

    unique_labels = np.unique(labels_arr)
    unique_labels = unique_labels[unique_labels != background_label]

    if per_cluster and cluster_labels is not None:
        rows = []
        for rid in unique_labels:
            roi_and_thresh = (labels_arr == rid) & voxel_mask
            roi_cluster_labels = np.where(roi_and_thresh, cluster_labels, 0)
            roi_cluster_ids = np.unique(roi_cluster_labels)
            roi_cluster_ids = roi_cluster_ids[roi_cluster_ids > 0]
            if len(roi_cluster_ids) == 0:
                continue
            cluster_roi_voxels = [
                (cid, np.sum(roi_cluster_labels == cid))
                for cid in roi_cluster_ids
            ]
            cluster_roi_voxels.sort(key=lambda x: -x[1])
            for rank, (cid, nv) in enumerate(cluster_roi_voxels, 1):
                mask = roi_cluster_labels == cid
                mean_val = float(np.mean(data_arr[mask]))
                rows.append((int(rid), rank, int(nv), mean_val))
        return rows

    region_ids = []
    means = []
    for rid in unique_labels:
        roi_mask = (labels_arr == rid) & voxel_mask
        values = data_arr[roi_mask]
        if len(values) > 0:
            means.append(float(np.mean(values)))
        else:
            means.append(np.nan)
        region_ids.append(int(rid))
    return region_ids, means


def main(sub_brick=3, output_path=None, threshold=None, cluster_size=None):
    """Extract mean betas for specified sub-brick. sub_brick 3 = Z~Pos.
    If threshold is set, only voxels exceeding it are averaged per ROI.
    If cluster_size is set, only voxels in clusters of at least that many voxels are included."""
    atlas_path = os.path.join(DATA_DIR, HASKINS_ATLAS)
    group_map_path = os.path.join(DATA_DIR, GROUP_MAP)

    if not os.path.exists(atlas_path):
        print(f"Error: Atlas not found at {atlas_path}")
        print("Place HaskinsPeds_NL_atlas1.01.nii.gz in the data/ directory.")
        sys.exit(1)
    if not os.path.exists(group_map_path):
        print(f"Error: Group map not found at {group_map_path}")
        print("Place KidVid_group_prelim_030526+tlrc.HEAD and .BRIK in the data/ directory.")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Loading group map...")
    img = nib.load(group_map_path)
    data = img.get_fdata()
    beta_3d = Nifti1Image(data[..., sub_brick], img.affine)
    atlas_img = nib.load(atlas_path)

    lut = load_label_lut(atlas_path)

    if threshold is not None:
        msg = f"Extracting mean of voxels > {threshold} per ROI"
        if cluster_size is not None:
            msg += f" (cluster size >= {cluster_size} voxels)"
            msg += ", one row per cluster"
        print(msg + "...")
        result = extract_thresholded_means(
            beta_3d, atlas_img, threshold,
            cluster_size=cluster_size,
            per_cluster=(cluster_size is not None),
        )
        if cluster_size is not None:
            rows = result
            region_ids = [r[0] for r in rows]
            region_names = [
                f"{lut.get(r[0], f'region_{r[0]}')}_cluster{r[1]}"
                for r in rows
            ]
            region_names_short = [lut.get(r[0], f"region_{r[0]}") for r in rows]
            cluster_ranks = [r[1] for r in rows]
            n_voxels = [r[2] for r in rows]
            mean_betas_flat = [r[3] for r in rows]
            df = pd.DataFrame({
                "region_id": region_ids,
                "region_name": region_names_short,
                "cluster_rank": cluster_ranks,
                "label": region_names,
                "n_voxels": n_voxels,
                "mean_beta": mean_betas_flat,
            })
        else:
            region_ids, mean_betas_flat = result
            region_names = [lut.get(rid, f"region_{rid}") for rid in region_ids]
            df = pd.DataFrame({
                "region_id": region_ids,
                "region_name": region_names,
                "mean_beta": mean_betas_flat,
            })
    else:
        print("Creating NiftiLabelsMasker with HaskinsPeds atlas...")
        masker = NiftiLabelsMasker(
            labels_img=atlas_path,
            strategy="mean",
            standardize=False,
            resampling_target="data",
        )
        masker.fit(beta_3d)
        print("Extracting mean betas...")
        mean_betas = masker.transform(beta_3d)
        mean_betas_flat = mean_betas.flatten()
        region_ids_ = masker.region_ids_
        region_ids = [region_ids_[i] for i in range(len(mean_betas_flat))]
        region_names = [lut.get(rid, f"region_{rid}") for rid in region_ids]
        df = pd.DataFrame({
            "region_id": region_ids,
            "region_name": region_names,
            "mean_beta": mean_betas_flat,
        })

    if output_path is None:
        output_path = os.path.join(OUTPUT_DIR, "KidVid_group_Z_Pos_roi_betas.csv")
    df.to_csv(output_path, index=False)
    if cluster_size is not None and threshold is not None:
        print(f"\nSaved {len(df)} region-cluster rows to:\n  {output_path}")
    else:
        print(f"\nSaved {len(df)} ROI mean betas to:\n  {output_path}")
    print(df.head(15).to_string())
    return df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract mean betas from Haskins atlas ROIs")
    parser.add_argument("-s", "--sub-brick", type=int, default=3,
                        help="Sub-brick index (default: 3 = Z~Pos)")
    parser.add_argument("-t", "--threshold", type=float, default=None,
                        help="Only average voxels exceeding this value (default: all voxels)")
    parser.add_argument("-c", "--cluster-size", type=int, default=None,
                        help="Minimum cluster size in voxels (requires -t; 26-connectivity)")
    parser.add_argument("-o", "--output", default=None, help="Output CSV path")
    args = parser.parse_args()
    if args.cluster_size is not None and args.threshold is None:
        parser.error("--cluster-size requires --threshold")
    main(
        sub_brick=args.sub_brick,
        output_path=args.output,
        threshold=args.threshold,
        cluster_size=args.cluster_size,
    )
