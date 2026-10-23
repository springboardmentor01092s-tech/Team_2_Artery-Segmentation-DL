"""Geometry-aware research volume preparation, separate from 2D XCA inference.

SimpleITK uses x/y/z physical LPS coordinates; NumPy tensors use z/y/x order.
No automatic anatomical ROI, patient identity inference, or model prediction.
"""
from pathlib import Path

import numpy as np
import SimpleITK as sitk

MAX_VOXELS = 32_000_000


def geometry(image):
    return {"size_xyz": list(image.GetSize()), "spacing_xyz_mm": list(image.GetSpacing()),
            "origin_lps_mm": list(image.GetOrigin()), "direction_lps": list(image.GetDirection())}


def validate(image):
    if image.GetDimension() != 3 or image.GetNumberOfComponentsPerPixel() != 1:
        raise ValueError("A scalar 3D volume is required; 4D/time-series and vector data are unsupported")
    if np.prod(image.GetSize(), dtype=np.int64) > MAX_VOXELS or min(image.GetSize()) < 2:
        raise ValueError("Volume must have at least two voxels per axis and at most 32 million voxels")
    if not np.all(np.isfinite(image.GetSpacing())) or min(image.GetSpacing()) <= 0:
        raise ValueError("Positive finite voxel spacing is required")
    direction = np.asarray(image.GetDirection()).reshape(3, 3)
    if not np.all(np.isfinite(image.GetOrigin())) or not np.allclose(direction.T @ direction, np.eye(3), atol=1e-4):
        raise ValueError("Invalid origin or non-orthonormal direction matrix")
    if not np.isfinite(sitk.GetArrayViewFromImage(image)).all():
        raise ValueError("Volume contains non-finite intensities")


def read_volume(path: Path):
    """Read NIfTI or one unambiguous, de-identified DICOM series directory."""
    if path.is_dir():
        import pydicom
        series = sitk.ImageSeriesReader.GetGDCMSeriesIDs(str(path)) or []
        if len(series) != 1:
            raise ValueError("Provide a directory containing exactly one DICOM series")
        files = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(str(path), series[0])
        if not files:
            raise ValueError("DICOM series contains no slices")
        positions = []
        for file in files:
            ds = pydicom.dcmread(file, stop_before_pixels=True)
            if int(ds.Rows)*int(ds.Columns)*len(files) > MAX_VOXELS:
                raise ValueError("DICOM volume exceeds the 32-million-voxel limit")
            if any(str(getattr(ds, tag, "")).strip() for tag in
                   ("PatientName", "PatientID", "PatientBirthDate", "PatientAddress",
                    "PatientTelephoneNumbers", "ReferringPhysicianName")):
                raise ValueError("Remove identifying DICOM tags before preparation")
            if int(getattr(ds, "NumberOfFrames", 1)) != 1:
                raise ValueError("Enhanced multi-frame DICOM volumes require a dedicated importer")
            orientation = np.asarray(ds.ImageOrientationPatient, dtype=float)
            position = np.asarray(ds.ImagePositionPatient, dtype=float)
            if positions and not np.allclose(orientation, first_orientation, atol=1e-4):
                raise ValueError("DICOM slice orientations differ")
            first_orientation = orientation
            positions.append(float(position @ np.cross(orientation[:3], orientation[3:])))
        differences = np.diff(positions)
        if len(differences) and (np.any(np.abs(differences) < 1e-5) or
                                not np.allclose(differences, differences[0], rtol=.01, atol=.01)):
            raise ValueError("Duplicate or irregularly spaced DICOM slices; do not stack automatically")
        reader = sitk.ImageSeriesReader()
        reader.SetFileNames(files)
        reader.SetNumberOfThreads(1)
        image = reader.Execute()
    else:
        if not str(path).lower().endswith((".nii", ".nii.gz")):
            raise ValueError("Use NIfTI .nii/.nii.gz or a de-identified DICOM series directory")
        import nibabel as nib
        header = nib.load(str(path)).header
        if header.get_xyzt_units()[0] != "mm":
            raise ValueError("NIfTI spatial units must explicitly be millimetres; do not guess voxel units")
        reader = sitk.ImageFileReader()
        reader.SetFileName(str(path))
        reader.ReadImageInformation()
        if reader.GetDimension() != 3 or np.prod(reader.GetSize(), dtype=np.int64) > MAX_VOXELS:
            raise ValueError("Only 3D volumes up to 32 million voxels are supported")
        reader.SetNumberOfThreads(1)
        image = reader.Execute()
    validate(image)
    return image


def register_rigid(moving, fixed):
    """Explicit opt-in rigid physical registration; always requires visual QC."""
    validate(moving)
    validate(fixed)
    moving = sitk.Cast(moving, sitk.sitkFloat32)
    fixed = sitk.Cast(fixed, sitk.sitkFloat32)
    if np.std(sitk.GetArrayViewFromImage(moving)) < 1e-6 or np.std(sitk.GetArrayViewFromImage(fixed)) < 1e-6:
        raise ValueError("Registration requires non-constant image intensities")
    initial = sitk.CenteredTransformInitializer(fixed, moving, sitk.Euler3DTransform(),
                                               sitk.CenteredTransformInitializerFilter.GEOMETRY)
    method = sitk.ImageRegistrationMethod()
    method.SetNumberOfThreads(1)
    method.SetMetricAsMattesMutualInformation(32)
    method.SetMetricSamplingStrategy(method.RANDOM)
    method.SetMetricSamplingPercentage(.2, 42)
    method.SetInterpolator(sitk.sitkLinear)
    method.SetOptimizerAsRegularStepGradientDescent(1., .001, 100)
    method.SetOptimizerScalesFromPhysicalShift()
    method.SetShrinkFactorsPerLevel([2, 1])
    method.SetSmoothingSigmasPerLevel([1, 0])
    method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()
    method.SetInitialTransform(initial, inPlace=False)
    transform = method.Execute(fixed, moving)
    if not np.isfinite(method.GetMetricValue()):
        raise ValueError("Registration failed: non-finite similarity metric")
    return transform, {"metric": float(method.GetMetricValue()),
                       "optimizer_stop": method.GetOptimizerStopConditionDescription(),
                       "quality_control_required": True, "transform_maps": "fixed LPS to moving LPS"}


def prepare_volume(image, *, spacing=None, roi=None, denoise=False, enhance=False,
                   mask=None, reference=None, slice_axis=2, slice_index=None):
    validate(image)
    source_geometry = geometry(image)
    image = sitk.Cast(image, sitk.sitkFloat32)
    steps = ["volume_validation"]
    if mask is not None:
        validate(mask)
        if geometry(mask) != geometry(image):
            raise ValueError("Mask geometry must exactly match the source image")
        labels = np.unique(sitk.GetArrayViewFromImage(mask))
        if np.any(labels < 0) or not np.all(labels == np.floor(labels)):
            raise ValueError("Masks must contain non-negative categorical integer labels")
    transform = None
    registration = None
    if reference is not None:
        transform, registration = register_rigid(image, reference)
        image = sitk.Resample(image, reference, transform, sitk.sitkLinear, 0., sitk.sitkFloat32)
        if mask is not None:
            mask = sitk.Resample(mask, reference, transform, sitk.sitkNearestNeighbor, 0.)
        steps.append("opt_in_rigid_registration_to_reference")
    values = sitk.GetArrayFromImage(image).astype(np.float32)
    low, high = np.percentile(values, [1, 99])
    values = np.clip((values - low) / max(float(high-low), 1e-6), 0, 1)
    normalized = sitk.GetImageFromArray(values)
    normalized.CopyInformation(image)
    image = normalized
    steps.append("percentile_intensity_normalization_0_1")
    if denoise:
        filt = sitk.MedianImageFilter()
        filt.SetRadius([1, 1, 1])
        filt.SetNumberOfThreads(1)
        image = filt.Execute(image)
        steps.append("optional_3d_median_noise_reduction")
    if enhance:
        filt = sitk.AdaptiveHistogramEqualizationImageFilter()
        filt.SetRadius([2, 2, 2])
        filt.SetAlpha(.3)
        filt.SetBeta(.3)
        filt.SetNumberOfThreads(1)
        image = sitk.Clamp(filt.Execute(image), lowerBound=0., upperBound=1.)
        steps.append("optional_local_contrast_enhancement")
    if roi is not None:
        if len(roi) != 6 or any(int(v) != v for v in roi):
            raise ValueError("ROI must be integer x,y,z,width,height,depth")
        start, size = list(roi[:3]), list(roi[3:])
        if any(start[i] < 0 or size[i] < 2 or start[i] + size[i] > image.GetSize()[i] for i in range(3)):
            raise ValueError("ROI is outside the volume or smaller than two voxels per axis")
        image = sitk.RegionOfInterest(image, size, start)
        if mask is not None:
            mask = sitk.RegionOfInterest(mask, size, start)
        steps.append("physical_origin_preserving_roi_crop")
    if spacing is not None:
        if len(spacing) != 3 or not np.isfinite(spacing).all() or min(spacing) <= 0:
            raise ValueError("Target spacing must be three positive finite values in mm")
        # Preserve voxel-centre endpoints by recording actual spacing after rounding.
        extent = (np.asarray(image.GetSize())-1)*image.GetSpacing()
        size = np.maximum(2, np.rint(extent/np.asarray(spacing)).astype(int)+1)
        if np.prod(size, dtype=np.int64) > MAX_VOXELS:
            raise ValueError("Requested resolution exceeds the 32-million-voxel limit")
        actual = extent/(size-1)
        grid = sitk.Image([int(v) for v in size], sitk.sitkFloat32)
        grid.SetOrigin(image.GetOrigin())
        grid.SetDirection(image.GetDirection())
        grid.SetSpacing([float(v) for v in actual])
        image = sitk.Resample(image, grid, sitk.Transform(), sitk.sitkLinear, 0.)
        if mask is not None:
            mask = sitk.Resample(mask, grid, sitk.Transform(), sitk.sitkNearestNeighbor, 0.)
        steps.append("physical_extent_preserving_resolution_resampling")
    if slice_axis not in (0, 1, 2):
        raise ValueError("Slice axis must be 0 (x), 1 (y), or 2 (z)")
    index = image.GetSize()[slice_axis]//2 if slice_index is None else slice_index
    if index < 0 or index >= image.GetSize()[slice_axis]:
        raise ValueError("Slice index is outside the prepared volume")
    tensor = sitk.GetArrayFromImage(image).astype(np.float32)[None]
    selected = np.take(tensor[0], index, axis=2-slice_axis)[None]
    record = {"pipeline_version": "volume-1.0", "source_geometry": source_geometry,
              "prepared_geometry": geometry(image), "normalization_percentiles": [float(low), float(high)],
              "requested_spacing_xyz_mm": spacing, "roi_xyz_size": roi,
              "slice_axis_xyz": slice_axis, "slice_index": index,
              "model_input_shape_czyx": list(tensor.shape), "slice_input_shape_chw": list(selected.shape),
              "steps": steps, "registration": registration,
              "warnings": ["Research preparation only; no compatible trained 3D model is invoked",
                           "Verify de-identification and visually inspect geometry and fine vessel detail"],
              "augmentation": "Not applied: use training-only paired augmentation, never validation/test"}
    return image, mask, tensor, selected, record, transform


def augment_training_volume(image, mask, *, seed, split):
    """Seeded paired small rigid augmentation on an unchanged physical grid."""
    if split != "train":
        raise ValueError("Augmentation is permitted only for the training split")
    validate(image)
    validate(mask)
    if geometry(image) != geometry(mask):
        raise ValueError("Image and mask geometry differ")
    rng = np.random.default_rng(seed)
    transform = sitk.Euler3DTransform()
    transform.SetCenter(image.TransformContinuousIndexToPhysicalPoint([(s-1)/2 for s in image.GetSize()]))
    transform.SetRotation(*rng.uniform(-.05, .05, 3))
    transform.SetTranslation(tuple(rng.uniform(-1., 1., 3)))
    return (sitk.Resample(image, image, transform, sitk.sitkLinear, 0.),
            sitk.Resample(mask, mask, transform, sitk.sitkNearestNeighbor, 0.))
