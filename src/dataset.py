"""Manifest-based random-patch dataset, following the Kaggle notebook."""
from pathlib import Path
import numpy as np
import pandas as pd
try:
    import SimpleITK as sitk
except ImportError:
    sitk = None
import torch
from torch.utils.data import Dataset

from .preprocessing import normalize_ct


def sample_patch(ct, mask, patch_size=(64, 128, 128), foreground_probability=0.7,
                 rng=None):
    """Sample paired patches from arrays in (Z,Y,X) order."""
    if ct.shape != mask.shape:
        raise ValueError(f"CT/mask shape mismatch: {ct.shape} vs {mask.shape}")
    pz, py, px = patch_size
    pads = [(0, max(0, p - n)) for n, p in zip(ct.shape, patch_size)]
    if any(right > 0 for _, right in pads):
        ct = np.pad(ct, pads, mode="constant", constant_values=0)
        mask = np.pad(mask, pads, mode="constant", constant_values=0)
    zmax, ymax, xmax = ct.shape
    rng = rng or np.random.default_rng()

    if rng.random() < foreground_probability:
        coords = np.argwhere(mask > 0)
        if len(coords):
            cz, cy, cx = coords[rng.integers(len(coords))]
        else:
            cz, cy, cx = zmax // 2, ymax // 2, xmax // 2
    else:
        cz, cy, cx = rng.integers(zmax), rng.integers(ymax), rng.integers(xmax)

    z0 = int(np.clip(cz - pz // 2, 0, zmax - pz))
    y0 = int(np.clip(cy - py // 2, 0, ymax - py))
    x0 = int(np.clip(cx - px // 2, 0, xmax - px))
    return (
        ct[z0:z0+pz, y0:y0+py, x0:x0+px].astype(np.float32, copy=True),
        (mask[z0:z0+pz, y0:y0+py, x0:x0+px] > 0).astype(np.float32, copy=True),
    )


class CoroVisionPatchDataset(Dataset):
    """
    CSV columns required: case_id,image_path,mask_path,split.
    image_path should point to the notebook's normalized CT volume.
    mask_path should point to the corrected mask candidate that has been
    anatomically checked; this loader does not reverse masks automatically.
    """

    def __init__(self, manifest_path, split, patches_per_case=4,
                 patch_size=(64, 128, 128), foreground_probability=0.7,
                 fixed_seed=None, raw_ct=False, cache_in_memory=True):
        self.manifest_path = Path(manifest_path).resolve()
        self.patch_size = tuple(patch_size)
        self.patches_per_case = int(patches_per_case)
        self.foreground_probability = float(foreground_probability)
        self.fixed_seed = fixed_seed
        self.raw_ct = bool(raw_ct)
        self.cache_in_memory = bool(cache_in_memory)
        self._cache = {}

        df = pd.read_csv(self.manifest_path)
        required = {"case_id", "image_path", "mask_path", "split"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Manifest missing columns: {sorted(missing)}")
        df = df[df["split"].astype(str).str.lower() == split.lower()].copy()
        if df.empty:
            raise ValueError(f"No cases found for split={split!r}")
        if df["case_id"].duplicated().any():
            raise ValueError("case_id values must be unique within manifest")

        self.records = []
        for _, row in df.iterrows():
            record = row.to_dict()
            for key in ("image_path", "mask_path"):
                p = Path(str(record[key]))
                if not p.is_absolute():
                    p = self.manifest_path.parent / p
                p = p.resolve()
                if not p.is_file():
                    raise FileNotFoundError(f"{key} for {record['case_id']}: {p}")
                record[key] = str(p)
            self.records.append(record)

    def __len__(self):
        return len(self.records) * self.patches_per_case

    def __getitem__(self, index):
        case_index = index // self.patches_per_case
        record = self.records[case_index]

        if self.cache_in_memory and case_index in self._cache:
            ct, mask = self._cache[case_index]
        else:
            if sitk is None:
                raise ImportError("SimpleITK is required for NIfTI image operations. Install with: pip install SimpleITK")
            ct_img = sitk.ReadImage(record["image_path"])
            mask_img = sitk.ReadImage(record["mask_path"])
            ct = sitk.GetArrayFromImage(ct_img).astype(np.float32)
            mask = sitk.GetArrayFromImage(mask_img)

            if self.raw_ct:
                ct = normalize_ct(ct)
            if ct.shape != mask.shape:
                raise ValueError(f"{record['case_id']}: CT/mask shapes differ")
            if not np.isfinite(ct).all():
                raise ValueError(f"{record['case_id']}: CT contains non-finite values")
            if np.count_nonzero(mask) == 0:
                raise ValueError(f"{record['case_id']}: mask is empty")
            if not set(np.unique(mask).tolist()).issubset({0, 1}):
                mask = (mask > 0).astype(np.uint8)

            if self.cache_in_memory:
                self._cache[case_index] = (ct, mask)

        if self.fixed_seed is None:
            rng = np.random.default_rng()
        else:
            rng = np.random.default_rng(self.fixed_seed + index)

        image_patch, mask_patch = sample_patch(
            ct, mask, self.patch_size, self.foreground_probability, rng
        )
        return (
            torch.from_numpy(image_patch[None]).float(),
            torch.from_numpy(mask_patch[None]).float(),
            str(record["case_id"]),
        )


def load_case_from_record(record, atol_origin=1e-2, atol_geom=1e-3):
    """Load full CT/mask arrays and image metadata for full-volume evaluation."""
    if sitk is None:
        raise ImportError("SimpleITK is required for NIfTI image operations. Install with: pip install SimpleITK")
    ct_img = sitk.ReadImage(record["image_path"])
    mask_img = sitk.ReadImage(record["mask_path"])
    ct = sitk.GetArrayFromImage(ct_img).astype(np.float32)
    mask = sitk.GetArrayFromImage(mask_img) > 0
    if ct.shape != mask.shape:
        raise ValueError(f"{record['case_id']}: CT/mask shapes differ")

    origin_close = np.allclose(ct_img.GetOrigin(), mask_img.GetOrigin(), atol=atol_origin)
    spacing_close = np.allclose(ct_img.GetSpacing(), mask_img.GetSpacing(), atol=atol_geom)
    direction_close = np.allclose(ct_img.GetDirection(), mask_img.GetDirection(), atol=atol_geom)

    if not (origin_close and spacing_close and direction_close):
        raise ValueError(
            f"{record['case_id']}: CT/mask physical geometry differs beyond tolerance. "
            "Verify alignment before evaluation."
        )
    return ct, mask, ct_img
