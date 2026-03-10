#!/usr/bin/env python3
"""
Extract mean beta/signal from HaskinsPeds atlas ROIs for individual subjects.
Output: CSV with rows = Haskins ROIs, columns = subjects.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DATA_DIR, OUTPUT_DIR, HASKINS_ATLAS, STATS_FILE_PATTERN, SUBJECT_LIST_FILE

import numpy as np
import nibabel as nib
from nibabel.nifti1 import Nifti1Image
from nilearn.image import check_niimg, resample_img
from nilearn.maskers import NiftiLabelsMasker
from nilearn._utils.niimg import safe_get_data
import pandas as pd


def load_label_lut(atlas_path):
    """
    Load label ID -> region name mapping. Uses HaskinsAtlas_LUT.txt for Haskins
    atlas (correct mapping); otherwise FreeSurfer LUT.
    """
    atlas_basename = os.path.basename(str(atlas_path)).lower()
    if "haskins" in atlas_basename:
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
    If per_cluster=True and cluster_size is set, returns one entry per cluster per ROI.
    Returns:
      - per_cluster=False: (region_ids, means)
      - per_cluster=True: list of (region_id, cluster_rank, n_voxels, mean)
    """
    from scipy import ndimage

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
        cluster_sizes = np.bincount(cluster_labels.ravel())[1:]
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


def main(
    subjects, sub_brick=7, output_path=None, data_dir=None, threshold=None, cluster_size=None
):
    """
    Extract mean betas for each subject. Rows = ROIs, columns = subjects.
    sub_brick: 7=Pos, 1=Neg, 4=Neut (for KidVid REML stats).
    If threshold is set, only voxels exceeding it are averaged per ROI.
    If cluster_size is set, only voxels in clusters of at least that many voxels are included.
    """
    data_dir = data_dir or DATA_DIR
    atlas_path = os.path.join(data_dir, HASKINS_ATLAS)
    if not os.path.exists(atlas_path):
        print(f"Error: Atlas not found at {atlas_path}")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Normalize subject IDs (ensure 3-digit format)
    subj_ids = []
    for s in subjects:
        sid = str(s).strip().zfill(3)  # 19 -> 019
        subj_ids.append(sid)

    # Find existing files
    valid_subjects = []
    missing = []
    for sid in subj_ids:
        fpath = os.path.join(data_dir, STATS_FILE_PATTERN.format(subj=sid))
        if os.path.exists(fpath):
            valid_subjects.append(sid)
        else:
            missing.append(sid)
    if missing:
        print(f"Warning: Files not found for subjects: {missing}")

    if not valid_subjects:
        print("Error: No valid subject files found.")
        print(f"Expected pattern: {STATS_FILE_PATTERN} in {DATA_DIR}")
        sys.exit(1)

    first_path = os.path.join(data_dir, STATS_FILE_PATTERN.format(subj=valid_subjects[0]))
    atlas_img = nib.load(atlas_path)
    lut = load_label_lut(atlas_path)

    if threshold is not None:
        msg = f"Extracting mean of voxels > {threshold} per ROI"
        if cluster_size is not None:
            msg += f" (cluster size >= {cluster_size} voxels)"
            msg += ", one row per cluster"
        print(msg + "...")
        result_lists = []
        for sid in valid_subjects:
            fpath = os.path.join(data_dir, STATS_FILE_PATTERN.format(subj=sid))
            print(f"  Processing sub-{sid}...")
            img = nib.load(fpath)
            beta_3d = Nifti1Image(img.get_fdata()[..., sub_brick], img.affine)
            result = extract_thresholded_means(
                beta_3d, atlas_img, threshold,
                cluster_size=cluster_size,
                per_cluster=(cluster_size is not None),
            )
            result_lists.append((sid, result))

        if cluster_size is not None:
            all_rows = set()
            subj_means = {}
            for sid, rows in result_lists:
                subj_means[sid] = {(r[0], r[1]): (r[2], r[3]) for r in rows}
                for r in rows:
                    all_rows.add((r[0], r[1]))
            all_rows = sorted(all_rows, key=lambda x: (x[0], x[1]))
            df_data = {
                "region_id": [r[0] for r in all_rows],
                "region_name": [lut.get(r[0], f"region_{r[0]}") for r in all_rows],
                "cluster_rank": [r[1] for r in all_rows],
                "label": [
                    f"{lut.get(r[0], f'region_{r[0]}')}_cluster{r[1]}"
                    for r in all_rows
                ],
            }
            n_voxels = []
            for r in all_rows:
                nv = np.nan
                for sid in valid_subjects:
                    if r in subj_means[sid]:
                        nv = subj_means[sid][r][0]
                        break
                n_voxels.append(nv)
            df_data["n_voxels"] = n_voxels
            for sid in valid_subjects:
                df_data[f"sub-{sid}"] = [
                    subj_means[sid].get(r, (np.nan, np.nan))[1] for r in all_rows
                ]
            df = pd.DataFrame(df_data)
        else:
            region_ids, _ = result_lists[0][1]
            region_names = [lut.get(rid, f"region_{rid}") for rid in region_ids]
            df = pd.DataFrame(
                {f"sub-{sid}": res[1] for sid, res in result_lists}
            )
            df.insert(0, "region_name", region_names)
            df.insert(0, "region_id", region_ids)
    else:
        print(f"Loading atlas and fitting masker (reference: sub-{valid_subjects[0]})...")
        first_img = nib.load(first_path)
        beta_ref = Nifti1Image(first_img.get_fdata()[..., sub_brick], first_img.affine)
        masker = NiftiLabelsMasker(
            labels_img=atlas_path,
            strategy="mean",
            standardize=False,
            resampling_target="data",
        )
        masker.fit(beta_ref)
        results = []
        for sid in valid_subjects:
            fpath = os.path.join(data_dir, STATS_FILE_PATTERN.format(subj=sid))
            print(f"  Processing sub-{sid}...")
            img = nib.load(fpath)
            beta_3d = Nifti1Image(img.get_fdata()[..., sub_brick], img.affine)
            mean_betas = masker.transform(beta_3d)
            results.append(mean_betas.flatten())
        n_out = len(results[0])
        region_ids_ = masker.region_ids_
        region_ids = [region_ids_[i] for i in range(n_out)]
        region_names = [lut.get(rid, f"region_{rid}") for rid in region_ids]
        df = pd.DataFrame(
            {f"sub-{sid}": vals for sid, vals in zip(valid_subjects, results)},
        )
        df.insert(0, "region_name", region_names)
        df.insert(0, "region_id", region_ids)

    if output_path is None:
        output_path = os.path.join(
            OUTPUT_DIR,
            f"roi_betas_subjects_subbrick{sub_brick}.csv",
        )
    output_path = os.path.abspath(output_path)
    df.to_csv(output_path, index=False)
    if cluster_size is not None and threshold is not None:
        print(f"\nSaved {len(df)} region-cluster rows x {len(valid_subjects)} subjects to:\n  {output_path}")
    else:
        print(f"\nSaved {len(df)} ROIs x {len(valid_subjects)} subjects to:\n  {output_path}")
    print(df.iloc[:5, :5].to_string())
    return df


def load_subject_list(path):
    """Load subject IDs from a text file (one per line)."""
    with open(path) as f:
        subjects = [
            line.strip() for line in f
            if line.strip() and not line.strip().startswith("#")
        ]
    return subjects


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Extract mean betas from Haskins atlas ROIs for individual subjects. "
        "Output: rows=ROIs, columns=subjects. Reads subject IDs from subject_list.txt by default."
    )
    parser.add_argument(
        "-f", "--subject-list",
        default=None,
        help="Path to subject list file (default: data/subject_list.txt or ./subject_list.txt)",
    )
    parser.add_argument(
        "-d", "--data-dir",
        default=None,
        help="Data directory (overrides HASKINS_DATA_DIR; use when stats files are elsewhere)",
    )
    parser.add_argument(
        "-s", "--sub-brick",
        type=int,
        default=7,
        help="Sub-brick index (default: 7=Pos, 1=Neg, 4=Neut for KidVid REML)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output CSV path",
    )
    parser.add_argument(
        "-t", "--threshold",
        type=float,
        default=None,
        help="Only average voxels exceeding this value (default: all voxels)",
    )
    parser.add_argument(
        "-c", "--cluster-size",
        type=int,
        default=None,
        help="Minimum cluster size in voxels (requires -t; 26-connectivity)",
    )
    args = parser.parse_args()
    if args.cluster_size is not None and args.threshold is None:
        parser.error("--cluster-size requires --threshold")

    # Override DATA_DIR if --data-dir specified
    data_dir = DATA_DIR
    if args.data_dir:
        data_dir = os.path.abspath(args.data_dir)
        print(f"Using data directory: {data_dir}")
        # Update config for main()
        import config
        config.DATA_DIR = data_dir

    # Resolve data dir and subject list path
    data_dir = DATA_DIR
    if args.data_dir:
        data_dir = os.path.abspath(args.data_dir)
        print(f"Using data directory: {data_dir}")

    if args.subject_list:
        subj_list_path = args.subject_list
    else:
        subj_list_path = os.path.join(data_dir, SUBJECT_LIST_FILE)
        if not os.path.exists(subj_list_path):
            subj_list_path = os.path.join(os.path.dirname(__file__), SUBJECT_LIST_FILE)

    if not os.path.exists(subj_list_path):
        print(f"Error: Subject list not found at {subj_list_path}")
        print("Create subject_list.txt with one subject ID per line (e.g., 019, 021, 024)")
        sys.exit(1)

    subjects = load_subject_list(subj_list_path)
    if not subjects:
        print(f"Error: No subjects found in {subj_list_path}")
        sys.exit(1)
    print(f"Loaded {len(subjects)} subjects from {subj_list_path}")

    main(
        subjects=subjects,
        sub_brick=args.sub_brick,
        output_path=args.output,
        data_dir=data_dir,
        threshold=args.threshold,
        cluster_size=args.cluster_size,
    )
