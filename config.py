"""
Configuration for Haskins atlas analysis scripts.
Set HASKINS_DATA_DIR environment variable to override the data directory.
"""
import os

# Directory containing neuroimaging data (atlas, template, group maps)
# Default: ./data relative to this package
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("HASKINS_DATA_DIR", os.path.join(SCRIPT_DIR, "data"))
OUTPUT_DIR = os.environ.get("HASKINS_OUTPUT_DIR", os.path.join(SCRIPT_DIR, "output"))

# File names (relative to DATA_DIR)
HASKINS_ATLAS = "HaskinsPeds_NL_atlas1.01.nii.gz"
HASKINS_TEMPLATE = "HaskinsPeds_NL_template1.0_SSW.nii"
FREESURFER_LUT = "FreeSurferColorLUT.txt"
GROUP_MAP = "KidVid_group_prelim_030526+tlrc.HEAD"
