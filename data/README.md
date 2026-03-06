# Data Directory

Place the following files in this directory to run the analysis scripts:

## Required Files

### For ROI extraction (`extract_roi_betas.py`) and group map visualization (`visualize_group_map.py`)

| File | Description | Source |
|------|-------------|--------|
| `KidVid_group_prelim_030526+tlrc.HEAD` | AFNI header for group statistical map | Your 3dLME output |
| `KidVid_group_prelim_030526+tlrc.BRIK` | AFNI data (binary) | Your 3dLME output |

### For atlas plotting (`plot_haskins_atlas.py`) and ROI extraction

| File | Description | Source |
|------|-------------|--------|
| `HaskinsPeds_NL_atlas1.01.nii.gz` | Haskins pediatric atlas (parcellation) | [AFNI atlases](https://afni.nimh.nih.gov/pub/dist/atlases/afni_atlases_dist/) |
| `HaskinsPeds_NL_template1.0_SSW.nii` | Haskins pediatric template | [AFNI atlases](https://afni.nimh.nih.gov/pub/dist/atlases/afni_atlases_dist/) |

### Optional

| File | Description |
|------|-------------|
| `FreeSurferColorLUT.txt` | Region name lookup table (included in repo root if not in data/) | [FreeSurfer](https://github.com/freesurfer/freesurfer) |

## Downloading the Haskins Atlas

If you have AFNI installed, the atlas may already be in your AFNI atlas path. Otherwise, download:

```bash
curl -O https://afni.nimh.nih.gov/pub/dist/atlases/afni_atlases_dist/HaskinsPeds_NL_atlas1.01+tlrc.HEAD
curl -O https://afni.nimh.nih.gov/pub/dist/atlases/afni_atlases_dist/HaskinsPeds_NL_atlas1.01+tlrc.BRIK.gz
gunzip HaskinsPeds_NL_atlas1.01+tlrc.BRIK.gz
```

Then convert to NIfTI using AFNI's `3dAFNItoNIFTI`:

```bash
3dAFNItoNIFTI -prefix HaskinsPeds_NL_atlas1.01 HaskinsPeds_NL_atlas1.01+tlrc.HEAD
```

Download the template:

```bash
curl -O https://afni.nimh.nih.gov/pub/dist/atlases/afni_atlases_dist/HaskinsPeds_NL_template1.0_SSW.nii.gz
gunzip HaskinsPeds_NL_template1.0_SSW.nii.gz
```
