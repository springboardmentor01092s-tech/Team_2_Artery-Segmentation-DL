"""
Dataset, DataLoader, and Preprocessing for DCA/ICA Coronary Angiograms.
"""

import os
import json
import random
import cv2
import numpy as np
import yaml
import torch
from torch.utils.data import Dataset, DataLoader


class CoronaryDataset(Dataset):
    """Loads coronary angiograms and masks with optional augmentation."""

    def __init__(self, case_ids: list, images_dir: str, masks_dir: str, augment: bool = False):
        self.case_ids = [str(c) for c in case_ids]
        self.images_dir = images_dir
        self.masks_dir = masks_dir
        self.augment = augment

    def __len__(self) -> int:
        return len(self.case_ids)

    def __getitem__(self, idx: int):
        case_id = self.case_ids[idx]
        img_p = os.path.join(self.images_dir, f"{case_id}.png")
        mask_p = os.path.join(self.masks_dir, f"{case_id}.png")

        img = cv2.imread(img_p, cv2.IMREAD_GRAYSCALE)
        mask = cv2.imread(mask_p, cv2.IMREAD_GRAYSCALE)
        if img is None or mask is None:
            raise FileNotFoundError(f"Missing case {case_id}: {img_p} or {mask_p}")

        if self.augment:
            if random.random() > 0.5:
                img, mask = np.fliplr(img), np.fliplr(mask)
            if random.random() > 0.5:
                img, mask = np.flipud(img), np.flipud(mask)
            k = random.choice([0, 1, 2, 3])
            if k > 0:
                img, mask = np.rot90(img, k), np.rot90(mask, k)

        img = (img.astype(np.float32) / 255.0)[None, ...]
        mask = ((mask.astype(np.float32) >= 128.0).astype(np.float32))[None, ...]

        return torch.from_numpy(img.copy()), torch.from_numpy(mask.copy()), case_id


def prepare_raw_dataset(raw_dir: str, target_size=(320, 320), output_base="dataset", seed=42):
    """Processes raw DCA/ICA .pgm files with CLAHE and symmetric padding."""
    random.seed(seed)
    images_out = os.path.join(output_base, "images")
    masks_out = os.path.join(output_base, "masks")
    os.makedirs(images_out, exist_ok=True)
    os.makedirs(masks_out, exist_ok=True)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    case_ids = []

    for f in sorted(os.listdir(raw_dir)):
        if not f.endswith(".pgm") or f.endswith("_gt.pgm"):
            continue
        case_id = f[:-4]
        gt_path = os.path.join(raw_dir, f"{case_id}_gt.pgm")
        if not os.path.exists(gt_path):
            continue

        img = cv2.imread(os.path.join(raw_dir, f), cv2.IMREAD_GRAYSCALE)
        mask = cv2.imread(gt_path, cv2.IMREAD_GRAYSCALE)
        if img is None or mask is None:
            continue

        h, w = img.shape
        pad_t, pad_b = (target_size[0] - h) // 2, target_size[0] - h - (target_size[0] - h) // 2
        pad_l, pad_r = (target_size[1] - w) // 2, target_size[1] - w - (target_size[1] - w) // 2

        img_pad = cv2.copyMakeBorder(clahe.apply(img), pad_t, pad_b, pad_l, pad_r, cv2.BORDER_REFLECT)
        mask_pad = cv2.copyMakeBorder(mask, pad_t, pad_b, pad_l, pad_r, cv2.BORDER_CONSTANT, value=0)

        cv2.imwrite(os.path.join(images_out, f"{case_id}.png"), img_pad)
        cv2.imwrite(os.path.join(masks_out, f"{case_id}.png"), (mask_pad >= 128).astype(np.uint8) * 255)
        case_ids.append(case_id)

    shuffled = case_ids.copy()
    random.shuffle(shuffled)
    n_train, n_val = int(len(shuffled) * 0.70), int(len(shuffled) * 0.15)

    splits = {
        "dataset_name": "DCA1_Coronary_Angiography",
        "total_count": len(case_ids),
        "native_size": [300, 300],
        "target_size": list(target_size),
        "seed": seed,
        "train": sorted(shuffled[:n_train], key=lambda x: int(x) if x.isdigit() else x),
        "val": sorted(shuffled[n_train:n_train + n_val], key=lambda x: int(x) if x.isdigit() else x),
        "test": sorted(shuffled[n_train + n_val:], key=lambda x: int(x) if x.isdigit() else x),
    }

    splits_path = os.path.join(output_base, "splits.json")
    with open(splits_path, "w") as fp:
        json.dump(splits, fp, indent=2)

    return splits


def get_dataloaders(config_path: str = "config.yaml"):
    """Loads config and returns DataLoaders for train, val, and test splits."""
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    img_dir, mask_dir = cfg["dataset"]["images_dir"], cfg["dataset"]["masks_dir"]
    with open(cfg["dataset"]["splits_file"], "r") as f:
        splits = json.load(f)

    batch_size = cfg["training"].get("batch_size", 8)
    loaders = []
    for split_key, is_train in [("train", True), ("val", False), ("test", False)]:
        ds = CoronaryDataset(splits[split_key], img_dir, mask_dir, augment=is_train)
        loaders.append(DataLoader(ds, batch_size=batch_size, shuffle=is_train, num_workers=0, pin_memory=True))

    return loaders[0], loaders[1], loaders[2], splits


if __name__ == "__main__":
    tr, vl, ts, sp = get_dataloaders()
    print(f"DataLoaders ready: Train={len(sp['train'])}, Val={len(sp['val'])}, Test={len(sp['test'])}")
    for x, y, ids in tr:
        print(f"Batch shape: image={x.shape}, mask={y.shape}, ids={ids[:3]}")
        break
