# Haskins Atlas Analysis

Python scripts for pediatric neuroimaging analysis using the [Haskins Pediatric Atlas](https://doi.org/10.1007/s00247-020-04875-y). This repository provides tools to:

1. **Extract mean signal** (e.g., beta values) from each Haskins atlas region → CSV output
2. **Visualize the atlas** as color-coded regions overlaid on the Haskins brain template
3. **Visualize group statistical maps** (e.g., from AFNI 3dLME)

## Requirements

- Python 3.8+
- [nilearn](https://nilearn.github.io/), nibabel, pandas, matplotlib

## Setup

```bash
# Clone or download this repository
cd haskins-atlas-analysis

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Data Setup

Place your neuroimaging data in the `data/` directory. See [data/README.md](data/README.md) for details.

**Quick setup** (if your data is in another folder):
```bash
./setup_data.sh /path/to/your/030326_group
```

**Required files:**
- `HaskinsPeds_NL_atlas1.01.nii.gz` – Haskins atlas parcellation
- `HaskinsPeds_NL_template1.0_SSW.nii` – Haskins brain template
- `KidVid_group_prelim_030526+tlrc.HEAD` and `.BRIK` – Group statistical map (AFNI format)

**Optional:** Set `HASKINS_DATA_DIR` to use a different data location:
```bash
export HASKINS_DATA_DIR=/path/to/your/data
```

## Usage

### 1. Extract mean signal per atlas region (group map)

Extracts the average value (e.g., Z-score, beta) within each Haskins ROI from a 3D/4D statistical map. Output: CSV with `region_id`, `region_name`, `mean_beta`.

```bash
python extract_roi_betas.py
# Default: sub-brick 3 (Z~Pos contrast)

# Specify different sub-brick (e.g., 5 = Z~Neut, 7 = Z~Neg)
python extract_roi_betas.py -s 5 -o output/Neut_roi_betas.csv

# Z threshold: only average voxels exceeding this value
python extract_roi_betas.py -s 3 -t 2.0 -o output/thresholded.csv

# Cluster size: only voxels in clusters of at least N voxels (requires -t)
python extract_roi_betas.py -s 3 -t 2.0 -c 10 -o output/clustered.csv

# Per-cluster output: one row per cluster per ROI (with -t and -c)
# Output includes region_id, region_name, cluster_rank, label, n_voxels, mean_beta
```

### 1b. Extract mean signal per atlas region (individual subjects)

Extracts mean beta for each subject. Output: CSV with **rows = Haskins ROIs**, **columns = subjects**.

Subject IDs are read from `subject_list.txt` (one ID per line). Copy `subject_list.txt.example` to `subject_list.txt` or `data/subject_list.txt` and add your subject IDs.

```bash
# Uses data/subject_list.txt (or ./subject_list.txt)
python extract_roi_betas_subjects.py

# Sub-brick: 7=Pos, 1=Neg, 4=Neut (KidVid REML)
python extract_roi_betas_subjects.py -s 7 -o output/Pos_by_subject.csv
python extract_roi_betas_subjects.py -s 1 -o output/Neg_by_subject.csv

# Z threshold and cluster size (per-cluster output when both used)
python extract_roi_betas_subjects.py -s 7 -t 1.5 -c 5 -o output/Pos_clustered.csv

# Custom subject list file
python extract_roi_betas_subjects.py -f /path/to/subject_list.txt

# Data in a different directory (e.g., 030326_group)
python extract_roi_betas_subjects.py -d /path/to/030326_group
```

### 2. Plot Haskins atlas overlay

Creates color-coded images of the atlas regions overlaid on the Haskins brain template.

```bash
python plot_haskins_atlas.py
# Output: output/HaskinsPeds_atlas_overlay.png, HaskinsPeds_atlas_overlay_tiled.png
```

### 3. Visualize group statistical maps

Plots individual contrast maps from the group analysis (e.g., Z~Pos, Z~Neg).

```bash
# Save Z~Pos (default) to file
python visualize_group_map.py -o output/group_Z_Pos.png

# Plot all Z-score contrasts
python visualize_group_map.py --all
```

## Output

| Script | Output |
|--------|--------|
| `extract_roi_betas.py` | `output/KidVid_group_Z_Pos_roi_betas.csv` |
| `extract_roi_betas_subjects.py` | `output/roi_betas_subjects_subbrick{N}.csv` (rows=ROIs, cols=subjects) |
| `plot_haskins_atlas.py` | `output/HaskinsPeds_atlas_overlay.png`, `output/HaskinsPeds_atlas_overlay_tiled.png` |
| `visualize_group_map.py` | `output/*.png` |

## Project Structure

```
haskins-atlas-analysis/
├── README.md
├── LICENSE
├── requirements.txt
├── setup_data.sh          # Copy data from source directory
├── config.py              # Path configuration
├── extract_roi_betas.py   # ROI extraction from group map → CSV
├── extract_roi_betas_subjects.py  # ROI extraction per subject → CSV
├── plot_haskins_atlas.py  # Atlas overlay plots
├── visualize_group_map.py # Group map visualization
├── HaskinsAtlas_LUT.txt   # Haskins region ID → name (used for atlas)
├── FreeSurferColorLUT.txt # FreeSurfer lookup (fallback for non-Haskins)
├── subject_list.txt.example  # Template for subject IDs
├── data/                  # Input data (see data/README.md)
│   └── README.md
└── output/                # Generated files (gitignored)
    └── .gitkeep
```

## References

- Molfese, P. J., et al. (2020). [The Haskins pediatric atlas: a magnetic-resonance-imaging-based pediatric template and atlas](https://doi.org/10.1007/s00247-020-04875-y). *Pediatric Radiology*, 51(4), 628–639.
- [Haskins Pediatric Atlas](https://afni.nimh.nih.gov/pub/dist/doc/htmldoc/template_atlas/sswarper_base.html)

## License

MIT License. The Haskins atlas and FreeSurfer LUT have their own licenses; see respective sources.
