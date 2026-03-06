#!/usr/bin/env python3
"""
Create an image of Haskins regions color-coded and overlaid on the Haskins brain.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DATA_DIR, OUTPUT_DIR, HASKINS_ATLAS, HASKINS_TEMPLATE

import nibabel as nib
from nibabel.nifti1 import Nifti1Image
from nilearn import plotting
import pandas as pd

# Use non-interactive backend for saving
import matplotlib
matplotlib.use("Agg")


def build_atlas_lut(lut_path):
    """Build pandas LUT with index and color (hex) for plot_roi."""
    if not os.path.exists(lut_path):
        return None
    rows = []
    with open(lut_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 5:
                try:
                    idx = int(parts[0])
                    r, g, b = int(parts[2]), int(parts[3]), int(parts[4])
                    hex_color = f"#{r:02x}{g:02x}{b:02x}"
                    rows.append({"index": idx, "name": parts[1], "color": hex_color})
                except (ValueError, IndexError):
                    continue
    return pd.DataFrame(rows) if rows else None


def main():
    template_path = os.path.join(DATA_DIR, HASKINS_TEMPLATE)
    atlas_path = os.path.join(DATA_DIR, HASKINS_ATLAS)
    lut_path = os.path.join(os.path.dirname(__file__), "FreeSurferColorLUT.txt")
    if not os.path.exists(lut_path):
        lut_path = os.path.join(DATA_DIR, "FreeSurferColorLUT.txt")

    if not os.path.exists(template_path):
        print(f"Error: Template not found at {template_path}")
        print("Place HaskinsPeds_NL_template1.0_SSW.nii in the data/ directory.")
        sys.exit(1)
    if not os.path.exists(atlas_path):
        print(f"Error: Atlas not found at {atlas_path}")
        print("Place HaskinsPeds_NL_atlas1.01.nii.gz in the data/ directory.")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Loading Haskins template and atlas...")
    template_img = nib.load(template_path)
    template_3d = Nifti1Image(template_img.get_fdata()[..., 0], template_img.affine)
    atlas_img = nib.load(atlas_path)

    lut = build_atlas_lut(lut_path)

    print("Creating overlay plot...")
    display = plotting.plot_roi(
        atlas_img,
        bg_img=template_3d,
        title="HaskinsPeds Atlas",
        cmap=lut if lut is not None else "gist_ncar",
        alpha=0.6,
        colorbar=True,
        display_mode="ortho",
        cut_coords=None,
        draw_cross=False,
    )
    ortho_path = os.path.join(OUTPUT_DIR, "HaskinsPeds_atlas_overlay.png")
    display.savefig(ortho_path, dpi=150, bbox_inches="tight")
    display.close()
    print(f"Saved: {ortho_path}")

    print("Creating tiled view...")
    display2 = plotting.plot_roi(
        atlas_img,
        bg_img=template_3d,
        title="HaskinsPeds Atlas (tiled)",
        cmap=lut if lut is not None else "gist_ncar",
        alpha=0.6,
        colorbar=True,
        display_mode="tiled",
        draw_cross=False,
    )
    tiled_path = os.path.join(OUTPUT_DIR, "HaskinsPeds_atlas_overlay_tiled.png")
    display2.savefig(tiled_path, dpi=120, bbox_inches="tight")
    display2.close()
    print(f"Saved: {tiled_path}")


if __name__ == "__main__":
    main()
