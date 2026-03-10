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

# Individual subject stats (from subject_list.txt)
SUBJ_LIST="$DATA_DIR/subject_list.txt"
[ ! -f "$SUBJ_LIST" ] && SUBJ_LIST="$(cd "$(dirname "$0")" && pwd)/subject_list.txt"
if [ -f "$SUBJ_LIST" ]; then
  while IFS= read -r s || [ -n "$s" ]; do
    s=$(echo "$s" | tr -d '[:space:]')
    [[ -z "$s" || "$s" =~ ^# ]] && continue
    # Pad to 3 digits if numeric (19 -> 019)
    [[ "$s" =~ ^[0-9]+$ ]] && [ "${#s}" -lt 3 ] && s=$(printf "%03d" "$((10#$s))")
    [ -f "$SOURCE/stats.sub-${s}_REML+tlrc.HEAD" ] && cp "$SOURCE/stats.sub-${s}_REML+tlrc.HEAD" "$DATA_DIR/"
    [ -f "$SOURCE/stats.sub-${s}_REML+tlrc.BRIK" ] && cp "$SOURCE/stats.sub-${s}_REML+tlrc.BRIK" "$DATA_DIR/"
  done < "$SUBJ_LIST"
  echo "Copied stats for subjects in subject_list.txt"
fi

# Haskins atlas and template
[ -f "$SOURCE/HaskinsPeds_NL_atlas1.01.nii.gz" ] && cp "$SOURCE/HaskinsPeds_NL_atlas1.01.nii.gz" "$DATA_DIR/"
[ -f "$SOURCE/HaskinsPeds_NL_template1.0_SSW.nii" ] && cp "$SOURCE/HaskinsPeds_NL_template1.0_SSW.nii" "$DATA_DIR/"

# FreeSurfer LUT (optional - already in repo root)
[ -f "$SOURCE/FreeSurferColorLUT.txt" ] && cp "$SOURCE/FreeSurferColorLUT.txt" "$DATA_DIR/"

echo "Done. Files in data/:"
ls -la "$DATA_DIR"
