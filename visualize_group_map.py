#!/usr/bin/env python3
"""
Visualize KidVid group map statistical maps using nilearn.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DATA_DIR, OUTPUT_DIR, GROUP_MAP

import nibabel as nib
from nibabel.nifti1 import Nifti1Image

# Sub-brick labels from AFNI HEAD file (KidVid 3dLME output)
SUBBRICK_LABELS = [
    "(Intercept)", "F~cond", "Coef~Pos", "Z~Pos", "Coef~Neut", "Z~Neut",
    "Coef~Neg", "Z~Neg", "Coef~Pos-Neut", "Z~Pos-Neut", "Coef~Neg-Neut",
    "Z~Neg-Neut", "Coef~Pos-Neg", "Z~Pos-Neg", "Coef~Emotion-Neut", "Z~Emotion-Neut",
]


def main():
    parser = argparse.ArgumentParser(description="Visualize KidVid group map")
    parser.add_argument("-s", "--sub-brick", type=int, default=3,
                        help="Sub-brick index (default: 3 = Z~Pos)")
    parser.add_argument("-o", "--output", default=None, help="Output PNG path")
    parser.add_argument("-t", "--threshold", type=float, default=2.0,
                        help="Z-score threshold (default: 2.0)")
    parser.add_argument("-a", "--all", action="store_true",
                        help="Save all Z-score sub-bricks")
    args = parser.parse_args()

    if args.output or args.all:
        import matplotlib
        matplotlib.use("Agg")

    from nilearn import plotting

    img_path = os.path.join(DATA_DIR, GROUP_MAP)
    if not os.path.exists(img_path):
        print(f"Error: Group map not found at {img_path}")
        sys.exit(1)

    img = nib.load(img_path)
    data = img.get_fdata()

    if args.all:
        z_indices = list(range(3, min(16, data.shape[-1]), 2))
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        for i in z_indices:
            label = SUBBRICK_LABELS[i] if i < len(SUBBRICK_LABELS) else f"Sub-brick {i}"
            vol = data[..., i]
            nii = Nifti1Image(vol, img.affine)
            out_file = os.path.join(OUTPUT_DIR, f"KidVid_group_subbrick{i}_{label.replace(' ', '_').replace('~', '-')}.png")
            plotting.plot_stat_map(nii, title=label, threshold=args.threshold,
                                  symmetric_cbar=True, output_file=out_file)
            print(f"Saved: {out_file}")
        return

    if args.sub_brick >= data.shape[-1]:
        print(f"Error: sub-brick {args.sub_brick} out of range")
        sys.exit(1)

    vol = data[..., args.sub_brick]
    nii = Nifti1Image(vol, img.affine)
    label = SUBBRICK_LABELS[args.sub_brick] if args.sub_brick < len(SUBBRICK_LABELS) else f"Sub-brick {args.sub_brick}"

    plot_kwargs = dict(title=label, threshold=args.threshold, symmetric_cbar=True)
    if args.output:
        plot_kwargs["output_file"] = args.output
        plotting.plot_stat_map(nii, **plot_kwargs)
        print(f"Saved: {args.output}")
    else:
        plotting.plot_stat_map(nii, **plot_kwargs)
        plotting.show()


if __name__ == "__main__":
    main()
