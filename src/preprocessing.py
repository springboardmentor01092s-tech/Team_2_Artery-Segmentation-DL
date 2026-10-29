"""Preprocessing helpers consistent with the notebook's CT intensity window."""
from pathlib import Path
import numpy as np
try:
    import SimpleITK as sitk
except ImportError:
    sitk = None


def normalize_ct(volume, lower=-200.0, upper=1000.0):
    """Notebook normalization: (clip(CT, -200, 1000) + 200) / 1200."""
    arr = np.asarray(volume, dtype=np.float32)
    arr = np.nan_to_num(arr, nan=lower, posinf=upper, neginf=lower)
    arr = np.clip(arr, lower, upper)
    return ((arr - lower) / (upper - lower)).astype(np.float32)


def read_sitk_array(path):
    """Read a SimpleITK image and return (Z,Y,X) array plus image metadata."""
    if sitk is None:
        raise ImportError("SimpleITK is required for NIfTI image operations. Install with: pip install SimpleITK")
    image = sitk.ReadImage(str(path))
    return sitk.GetArrayFromImage(image), image


def validate_pair(ct_image, mask_image, case_id="case", require_geometry=False):
    """Check shape and optionally exact physical geometry; never auto-corrects."""
    if sitk is None:
        raise ImportError("SimpleITK is required for NIfTI image operations. Install with: pip install SimpleITK")
    ct = sitk.GetArrayViewFromImage(ct_image)
    mask = sitk.GetArrayViewFromImage(mask_image)
    if ct.shape != mask.shape:
        raise ValueError(f"{case_id}: CT/mask array shapes differ: {ct.shape} vs {mask.shape}")

    geometry_equal = (
        ct_image.GetOrigin() == mask_image.GetOrigin()
        and ct_image.GetSpacing() == mask_image.GetSpacing()
        and ct_image.GetDirection() == mask_image.GetDirection()
    )
    if require_geometry and not geometry_equal:
        raise ValueError(f"{case_id}: CT and mask physical geometry differ.")
    return {
        "case_id": case_id,
        "shape_zyx": tuple(ct.shape),
        "geometry_equal": geometry_equal,
        "foreground_voxels": int(np.count_nonzero(mask)),
        "mask_labels": np.unique(mask).tolist(),
    }


def normalize_nifti_file(input_path, output_path):
    """Normalize a raw CT volume and save it preserving its SimpleITK geometry."""
    if sitk is None:
        raise ImportError("SimpleITK is required for NIfTI image operations. Install with: pip install SimpleITK")
    input_path, output_path = Path(input_path), Path(output_path)
    image = sitk.ReadImage(str(input_path))
    arr = sitk.GetArrayFromImage(image)
    normalized = normalize_ct(arr)
    out_image = sitk.GetImageFromArray(normalized)
    out_image.CopyInformation(image)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sitk.WriteImage(out_image, str(output_path))
    return output_path
