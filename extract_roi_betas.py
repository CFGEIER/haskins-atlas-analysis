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

import nibabel as nib
from nibabel.nifti1 import Nifti1Image
from nilearn.maskers import NiftiLabelsMasker
import pandas as pd


def load_freesurfer_lut():
    """Load FreeSurfer Color LUT: maps label ID -> region name."""
    lut_url = "https://raw.githubusercontent.com/freesurfer/freesurfer/dev/distribution/FreeSurferColorLUT.txt"
    # Check: repo root, data dir, FREESURFER_HOME
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


def main(sub_brick=3, output_path=None):
    """Extract mean betas for specified sub-brick. sub_brick 3 = Z~Pos."""
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

    lut = load_freesurfer_lut()
    region_names = [lut.get(rid, f"region_{rid}") for rid in region_ids]

    df = pd.DataFrame({
        "region_id": region_ids,
        "region_name": region_names,
        "mean_beta": mean_betas_flat,
    })

    if output_path is None:
        output_path = os.path.join(OUTPUT_DIR, "KidVid_group_Z_Pos_roi_betas.csv")
    df.to_csv(output_path, index=False)
    print(f"\nSaved {len(df)} ROI mean betas to:\n  {output_path}")
    print(df.head(15).to_string())
    return df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract mean betas from Haskins atlas ROIs")
    parser.add_argument("-s", "--sub-brick", type=int, default=3,
                        help="Sub-brick index (default: 3 = Z~Pos)")
    parser.add_argument("-o", "--output", default=None, help="Output CSV path")
    args = parser.parse_args()
    main(sub_brick=args.sub_brick, output_path=args.output)
