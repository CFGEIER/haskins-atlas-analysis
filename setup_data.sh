#!/bin/bash
# Copy data files from source directory to data/
# Usage: ./setup_data.sh /path/to/030326_group

SOURCE="${1:-/Users/cglab/Documents/030326_group}"
DATA_DIR="$(cd "$(dirname "$0")" && pwd)/data"

echo "Copying data from $SOURCE to $DATA_DIR"

mkdir -p "$DATA_DIR"

# Group map (AFNI)
[ -f "$SOURCE/KidVid_group_prelim_030526+tlrc.HEAD" ] && cp "$SOURCE/KidVid_group_prelim_030526+tlrc.HEAD" "$DATA_DIR/"
[ -f "$SOURCE/KidVid_group_prelim_030526+tlrc.BRIK" ] && cp "$SOURCE/KidVid_group_prelim_030526+tlrc.BRIK" "$DATA_DIR/"

# Haskins atlas and template
[ -f "$SOURCE/HaskinsPeds_NL_atlas1.01.nii.gz" ] && cp "$SOURCE/HaskinsPeds_NL_atlas1.01.nii.gz" "$DATA_DIR/"
[ -f "$SOURCE/HaskinsPeds_NL_template1.0_SSW.nii" ] && cp "$SOURCE/HaskinsPeds_NL_template1.0_SSW.nii" "$DATA_DIR/"

# FreeSurfer LUT (optional - already in repo root)
[ -f "$SOURCE/FreeSurferColorLUT.txt" ] && cp "$SOURCE/FreeSurferColorLUT.txt" "$DATA_DIR/"

echo "Done. Files in data/:"
ls -la "$DATA_DIR"
