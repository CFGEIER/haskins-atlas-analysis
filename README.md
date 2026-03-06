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

### 1. Extract mean signal per atlas region

Extracts the average value (e.g., Z-score, beta) within each Haskins ROI from a 3D/4D statistical map. Output: CSV with `region_id`, `region_name`, `mean_beta`.

```bash
python extract_roi_betas.py
# Default: sub-brick 3 (Z~Pos contrast)

# Specify different sub-brick (e.g., 5 = Z~Neut, 7 = Z~Neg)
python extract_roi_betas.py -s 5 -o output/Neut_roi_betas.csv
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
| `plot_haskins_atlas.py` | `output/HaskinsPeds_atlas_overlay.png`, `output/HaskinsPeds_atlas_overlay_tiled.png` |
| `visualize_group_map.py` | `output/*.png` |

## Project Structure

```
haskins-atlas-analysis/
├── README.md
├── requirements.txt
├── config.py              # Path configuration
├── extract_roi_betas.py   # ROI extraction → CSV
├── plot_haskins_atlas.py  # Atlas overlay plots
├── visualize_group_map.py # Group map visualization
├── FreeSurferColorLUT.txt # Region name lookup
├── data/                  # Input data (see data/README.md)
│   └── README.md
└── output/                # Generated files
    ├── KidVid_group_Z_Pos_roi_betas.csv
    ├── HaskinsPeds_atlas_overlay.png
    └── HaskinsPeds_atlas_overlay_tiled.png
```

## References

- Molfese, P. J., et al. (2020). [The Haskins pediatric atlas: a magnetic-resonance-imaging-based pediatric template and atlas](https://doi.org/10.1007/s00247-020-04875-y). *Pediatric Radiology*, 51(4), 628–639.
- [Haskins Pediatric Atlas](https://afni.nimh.nih.gov/pub/dist/doc/htmldoc/template_atlas/sswarper_base.html)

## License

MIT License. The Haskins atlas and FreeSurfer LUT have their own licenses; see respective sources.
