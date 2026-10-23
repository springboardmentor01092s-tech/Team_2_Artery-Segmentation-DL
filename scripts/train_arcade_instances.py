"""Instance-aware Mask R-CNN training and ARCADE-style evaluation.

Uses original ARCADE COCO polygons and category IDs. Training/model selection
consume train/val only; --evaluate-test is a separate, explicit final action.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw
from torch.utils.data import DataLoader, Dataset

ROOT = Path(__file__).resolve().parents[1]
TASK_CATEGORY = {"syntax": list(range(1, 26)), "stenosis": [26]}


def _pixel_digest(path: Path) -> str:
    """Hash decoded RGB pixels so different encodings of one frame still match."""
    with Image.open(path) as opened:
        image = opened.convert("RGB")
        digest = hashlib.sha256()
        digest.update(f"{image.width}x{image.height}:RGB:".encode())
        digest.update(image.tobytes())
        return digest.hexdigest()


class ArcadeInstances(Dataset):
    def __init__(self, task: str, split: str, input_size: int = 512, training: bool = False):
        self.task, self.split, self.input_size, self.training = task, split, input_size, training
        ann_path = ROOT / "arcade" / task / split / "annotations" / f"{split}.json"
        image_root = ann_path.parent.parent / "images"
        if not ann_path.is_file() or not image_root.is_dir():
            raise FileNotFoundError(f"Missing original ARCADE COCO data: {ann_path}")
        coco = json.loads(ann_path.read_text())
        self.images = sorted(coco["images"], key=lambda row: row["id"])
        self.excluded_train_duplicates: list[str] = []
        if split == "train":
            validation_root = ROOT / "arcade" / task / "val" / "images"
            image_suffixes = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
            validation_hashes = {
                _pixel_digest(path) for path in validation_root.glob("*")
                if path.is_file() and path.suffix.lower() in image_suffixes
            }
            kept_images = []
            for row in self.images:
                if _pixel_digest(image_root / row["file_name"]) in validation_hashes:
                    self.excluded_train_duplicates.append(row["file_name"])
                else:
                    kept_images.append(row)
            self.images = kept_images
            self.excluded_train_duplicates.sort()
        self.by_image = defaultdict(list)
        for annotation in coco["annotations"]:
            if annotation.get("iscrowd", 0) == 0 and annotation.get("segmentation"):
                self.by_image[annotation["image_id"]].append(annotation)
        self.image_root = image_root
        self.category_ids = TASK_CATEGORY[task]
        self.cat_to_label = {cat_id: i + 1 for i, cat_id in enumerate(self.category_ids)}
        self.categories = {row["id"]: row["name"] for row in coco["categories"]}
        self.annotation_json = coco
        self.image_records = {row["id"]: row for row in self.images}

    def __len__(self):
        return len(self.images)

    def __getitem__(self, index):
        info = self.images[index]
        image_id = info["id"]
        image = Image.open(self.image_root / info["file_name"]).convert("RGB")
        original_size = image.size
        if original_size != (self.input_size, self.input_size):
            image = image.resize((self.input_size, self.input_size), Image.Resampling.BILINEAR)
        image_np = np.asarray(image, dtype=np.float32) / 255.0
        if self.training:
            contrast = random.uniform(0.9, 1.1)
            brightness = random.uniform(-0.04, 0.04)
            image_np = np.clip((image_np - image_np.mean()) * contrast + image_np.mean() + brightness, 0, 1)
        masks, labels = [], []
        for ann in self.by_image[image_id]:
            cat_id = int(ann["category_id"])
            if cat_id not in self.cat_to_label:
                continue
            mask = Image.new("1", original_size, 0)
            draw = ImageDraw.Draw(mask)
            for polygon in ann["segmentation"]:
                if len(polygon) >= 6:
                    points = [(float(x), float(y)) for x, y in zip(polygon[::2], polygon[1::2])]
                    draw.polygon(points, fill=1)
            if original_size != (self.input_size, self.input_size):
                mask = mask.resize((self.input_size, self.input_size), Image.Resampling.NEAREST)
            masks.append(np.asarray(mask, dtype=np.uint8))
            labels.append(self.cat_to_label[cat_id])
        if masks:
            mask_array = np.stack(masks)
            boxes = []
            for mask in mask_array:
                ys, xs = np.where(mask > 0)
                boxes.append([xs.min(), ys.min(), xs.max() + 1, ys.max() + 1])
            masks_tensor = torch.as_tensor(mask_array, dtype=torch.uint8)
            boxes_tensor = torch.as_tensor(boxes, dtype=torch.float32)
            labels_tensor = torch.as_tensor(labels, dtype=torch.int64)
            area = masks_tensor.flatten(1).sum(1).to(torch.float32)
        else:
            masks_tensor = torch.zeros((0, self.input_size, self.input_size), dtype=torch.uint8)
            boxes_tensor = torch.zeros((0, 4), dtype=torch.float32)
            labels_tensor = torch.zeros((0,), dtype=torch.int64)
            area = torch.zeros((0,), dtype=torch.float32)
        target = {"boxes": boxes_tensor, "labels": labels_tensor, "masks": masks_tensor,
                  "image_id": torch.tensor(image_id), "area": area,
                  "iscrowd": torch.zeros((len(labels),), dtype=torch.int64)}
        return torch.from_numpy(image_np).permute(2, 0, 1), target, image_id


def collate(batch):
    return tuple(zip(*batch))


def build_detector(architecture: str, num_classes: int, pretrained: bool = True):
    from torchvision.models.detection import (MaskRCNN_ResNet50_FPN_Weights,
                                               MaskRCNN_ResNet50_FPN_V2_Weights,
                                               maskrcnn_resnet50_fpn,
                                               maskrcnn_resnet50_fpn_v2)
    from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
    from torchvision.models.detection.mask_rcnn import MaskRCNNPredictor
    if architecture == "maskrcnn_resnet50_fpn_v2":
        model = maskrcnn_resnet50_fpn_v2(weights=MaskRCNN_ResNet50_FPN_V2_Weights.DEFAULT if pretrained else None,
                                       weights_backbone=None)
    else:
        model = maskrcnn_resnet50_fpn(weights=MaskRCNN_ResNet50_FPN_Weights.DEFAULT if pretrained else None,
                                    weights_backbone=None)
        if not pretrained:
            # Evaluation loads the complete own checkpoint: never download a
            # second backbone. COCO v1 uses FrozenBN with eps=0, unlike the
            # random-weight builder's ordinary BN. Reproduce that architecture
            # explicitly before strict state loading.
            from torchvision.ops.misc import FrozenBatchNorm2d
            def frozen_norms(parent):
                for name, child in list(parent.named_children()):
                    if isinstance(child, torch.nn.BatchNorm2d):
                        setattr(parent, name, FrozenBatchNorm2d(child.num_features, eps=0.0))
                    else:
                        frozen_norms(child)
            frozen_norms(model.backbone.body)
    features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(features, num_classes)
    mask_features = model.roi_heads.mask_predictor.conv5_mask.in_channels
    model.roi_heads.mask_predictor = MaskRCNNPredictor(mask_features, 256, num_classes)
    return model


def polygon_f1(left, right):
    """ARCADE's polygon area F1, using the challenge's intersection/union semantics."""
    # Import outside the geometry fallback: a missing dependency must fail
    # loudly rather than score every prediction as zero.
    from shapely.geometry import Polygon

    try:
        predicted, ground_truth = Polygon(left), Polygon(right)
        try:
            overlap = predicted.intersection(ground_truth)
        except Exception:
            predicted, ground_truth = predicted.buffer(0), ground_truth.buffer(0)
            overlap = predicted.intersection(ground_truth)
        if overlap.geom_type == "MultiPolygon":
            polygons = [part for part in overlap.geoms if part.geom_type == "Polygon"]
            if not polygons:
                return 0.0
            overlap = max(polygons, key=lambda geom: geom.area)
        intersection = overlap.area
        if intersection <= 0:
            return 0.0
        false_positive = (predicted.buffer(0).difference(overlap)).area
        false_negative = (ground_truth.buffer(0).difference(overlap)).area
        precision = intersection / (intersection + false_positive)
        recall = intersection / (intersection + false_negative)
        return 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    except Exception:
        return 0.0


def mask_to_polygon(mask):
    from cv2 import RETR_EXTERNAL, CHAIN_APPROX_SIMPLE, findContours
    contours, _ = findContours(mask.astype(np.uint8), RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=lambda c: abs(__import__("cv2").contourArea(c)))
    points = contour.reshape(-1, 2)
    if len(points) < 3:
        return None
    return [(float(x), float(y)) for x, y in points]


def predict_one(model, image, device, score_threshold):
    model.eval()
    with torch.inference_mode():
        out = model([image.to(device)])[0]
    instances = []
    for i, score in enumerate(out["scores"].detach().cpu().numpy()):
        if score < score_threshold:
            continue
        mask_probability = out["masks"][i, 0].detach().cpu().numpy()
        binary = mask_probability >= 0.5
        polygon = mask_to_polygon(binary)
        if polygon is None:
            continue
        instances.append({"category_id": int(out["labels"][i].item()), "score": float(score),
                          "mask_probability": mask_probability, "mask": binary, "polygon": polygon})
    return instances


def official_score(task, dataset, predictions):
    """Reproduce the public ARCADE per-image/category scoring rules on COCO polygons."""
    scores = []
    annotations = dataset.annotation_json["annotations"]
    grouped = defaultdict(list)
    for ann in annotations:
        grouped[ann["image_id"]].append(ann)
    for info in dataset.images:
        image_id = info["id"]
        truth = grouped[image_id]
        pred = predictions.get(image_id, [])
        if task == "syntax":
            gt_classes = sorted(a["category_id"] for a in truth if a["category_id"] in TASK_CATEGORY[task])
            pred_classes = [item["category_id"] for item in pred]
            per_category = {}
            # Match the public syntax evaluator's first-GT-instance-per-class,
            # first-prediction-per-class behavior (including its handling of
            # predicted classes absent from the image's GT class list).
            for gt in truth:
                cat_id = gt["category_id"]
                if cat_id not in gt_classes:
                    continue
                for candidate in pred:
                    predicted_cat = candidate["category_id"]
                    if predicted_cat in gt_classes:
                        if predicted_cat == cat_id:
                            if cat_id in per_category:
                                continue
                            polygon = gt["segmentation"][0]
                            ground_truth_polygon = list(zip(polygon[::2], polygon[1::2]))
                            per_category[cat_id] = polygon_f1(ground_truth_polygon, candidate["polygon"])
                    else:
                        per_category[cat_id] = 0.0
            for cat_id in gt_classes:
                if cat_id not in pred_classes:
                    per_category[cat_id] = 0.0
            scores.append(float(np.mean(list(per_category.values()))) if per_category else 0.0)
        else:
            gt_for_task = [a for a in truth if a["category_id"] == 26]
            pred_for_task = [p for p in pred if p["category_id"] == 1]
            instance_scores = []
            for item in pred_for_task:
                best = 0.0
                for ann in gt_for_task:
                    poly = ann["segmentation"][0]
                    best = max(best, polygon_f1(list(zip(poly[::2], poly[1::2])), item["polygon"]))
                instance_scores.append(best)
            instance_scores.extend([0.0] * max(0, len(gt_for_task) - len(instance_scores)))
            scores.append(float(np.mean(instance_scores)) if instance_scores else 0.0)
    return float(np.mean(scores)) if scores else 0.0


def evaluate(model, dataset, device, score_threshold=0.25, pixel_threshold=0.5, max_images=None):
    model.eval()
    ids, preds = [], {}
    tp = fp = fn = tn = 0
    pos_hist = np.zeros(256, dtype=np.int64)
    neg_hist = np.zeros(256, dtype=np.int64)
    instance_tp = instance_fp = instance_fn = 0
    dice_values, iou_values = [], []
    count = min(len(dataset), max_images) if max_images else len(dataset)
    for index in range(count):
        image, target, image_id = dataset[index]
        output = predict_one(model, image, device, score_threshold)
        info = dataset.image_records[image_id]
        sx, sy = info["width"] / dataset.input_size, info["height"] / dataset.input_size
        for instance in output:
            instance["polygon"] = [(x * sx, y * sy) for x, y in instance["polygon"]]
        preds[image_id] = output
        ids.append(image_id)
        truth_masks = target["masks"].numpy().astype(bool)
        labels = target["labels"].numpy()
        h, w = truth_masks.shape[-2:]
        prob = np.zeros((h, w), dtype=np.float32)
        for item in output:
            prob = np.maximum(prob, item["mask_probability"])
        truth_union = truth_masks.any(axis=0) if len(truth_masks) else np.zeros((h, w), dtype=bool)
        prediction = prob >= pixel_threshold
        tp += int(np.count_nonzero(prediction & truth_union))
        fp += int(np.count_nonzero(prediction & ~truth_union))
        fn += int(np.count_nonzero(~prediction & truth_union))
        tn += int(np.count_nonzero(~prediction & ~truth_union))
        bins = np.minimum((prob * 256).astype(np.int32), 255)
        pos_hist += np.bincount(bins[truth_union], minlength=256)
        neg_hist += np.bincount(bins[~truth_union], minlength=256)
        gt_items = [(int(label), mask) for label, mask in zip(labels, truth_masks)]
        pred_items = [(item["category_id"], item["mask"]) for item in output]
        pairs = []
        for pi, (plabel, pmask) in enumerate(pred_items):
            for gi, (glabel, gmask) in enumerate(gt_items):
                if plabel == glabel:
                    inter = np.count_nonzero(pmask & gmask)
                    union = np.count_nonzero(pmask | gmask)
                    pairs.append((inter / max(union, 1), pi, gi))
        matched_p, matched_g = set(), set()
        for iou, pi, gi in sorted(pairs, reverse=True):
            if iou >= 0.5 and pi not in matched_p and gi not in matched_g:
                matched_p.add(pi); matched_g.add(gi)
                instance_tp += 1
                dice_values.append(2 * iou / (1 + iou))
                iou_values.append(iou)
        instance_fp += len(pred_items) - len(matched_p)
        instance_fn += len(gt_items) - len(matched_g)
    auc = histogram_auc(pos_hist, neg_hist)
    dice = 2 * tp / max(2 * tp + fp + fn, 1)
    pixel_iou = tp / max(tp + fp + fn, 1)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    return {"images": count,
            "arcade_official_f1": official_score(dataset.task, dataset, preds) if count == len(dataset) else None,
            "pixel_accuracy_union_mask": (tp + tn) / max(tp + fp + fn + tn, 1),
            "pixel_precision_union_mask": precision, "pixel_recall_sensitivity_union_mask": recall,
            "pixel_specificity_union_mask": tn / max(tn + fp, 1), "pixel_f1_union_mask": 2 * precision * recall / max(precision + recall, 1e-12),
            "pixel_dice_union_mask": dice, "pixel_iou_union_mask": pixel_iou, "pixel_auc_roc_union_score": auc,
            "instance_precision_iou50": instance_tp / max(instance_tp + instance_fp, 1),
            "instance_recall_iou50": instance_tp / max(instance_tp + instance_fn, 1),
            "instance_f1_iou50": 2 * instance_tp / max(2 * instance_tp + instance_fp + instance_fn, 1),
            "matched_instance_dice_iou50": float(np.mean(dice_values)) if dice_values else 0.0,
            "matched_instance_iou_iou50": float(np.mean(iou_values)) if iou_values else 0.0,
            "instance_counts": {"tp": instance_tp, "fp": instance_fp, "fn": instance_fn},
            "score_threshold": score_threshold, "pixel_threshold": pixel_threshold,
            "pixel_metric_note": "Supplementary binary-union pixel metrics; do not represent official ARCADE task scoring."}


def histogram_auc(positive, negative):
    if positive.sum() == 0 or negative.sum() == 0:
        return 0.0
    tpr = np.r_[0, np.cumsum(positive[::-1])] / positive.sum()
    fpr = np.r_[0, np.cumsum(negative[::-1])] / negative.sum()
    return float(np.trapezoid(tpr, fpr))


def train_one(task, architecture, args, device):
    train = ArcadeInstances(task, "train", args.input_size, training=True)
    val = ArcadeInstances(task, "val", args.input_size)
    train_loader = DataLoader(train, batch_size=args.batch_size, shuffle=True, num_workers=args.workers,
                              collate_fn=collate, pin_memory=device == "cuda")
    model = build_detector(architecture, len(TASK_CATEGORY[task]) + 1, pretrained=True).to(device)
    optimizer = torch.optim.SGD([p for p in model.parameters() if p.requires_grad], lr=args.lr,
                                momentum=0.9, weight_decay=0.0005)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=2)
    out_dir = args.output_root / task / architecture
    out_dir.mkdir(parents=True, exist_ok=True)
    best, best_metrics, stale, history = -1.0, {}, 0, []
    for epoch in range(args.epochs):
        started = time.perf_counter()
        model.train()
        loss_sum = 0.0
        for images, targets, _ in train_loader:
            images = [im.to(device) for im in images]
            targets = [{key: value.to(device) for key, value in target.items()} for target in targets]
            loss_parts = model(images, targets)
            loss = sum(loss_parts.values())
            if not torch.isfinite(loss):
                raise RuntimeError(f"Non-finite instance loss in {task}/{architecture} at epoch {epoch + 1}")
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            gradient_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            if not torch.isfinite(gradient_norm):
                raise RuntimeError(f"Non-finite instance gradients in {task}/{architecture} at epoch {epoch + 1}")
            optimizer.step()
            loss_sum += float(loss.item())
        metrics = evaluate(model, val, device, args.score_threshold, args.pixel_threshold, args.val_limit)
        # Official ARCADE task F1 is the primary checkpoint objective.
        selection = metrics["arcade_official_f1"]
        row = {"epoch": epoch + 1, "mean_train_loss": loss_sum / max(len(train_loader), 1),
               "learning_rate": optimizer.param_groups[0]["lr"], "epoch_seconds": time.perf_counter() - started,
               "selection_score_official_f1": selection, "validation": metrics}
        history.append(row)
        print(json.dumps({"task": task, "architecture": architecture, **row}), flush=True)
        if selection is not None:
            scheduler.step(selection)
        if selection is not None and selection > best:
            best, best_metrics, stale = selection, metrics, 0
            torch.save({"state_dict": model.state_dict(), "task": task, "architecture": architecture,
                        "num_classes": len(TASK_CATEGORY[task]) + 1, "input_size": args.input_size,
                        "category_ids": TASK_CATEGORY[task], "epoch": epoch + 1}, out_dir / "best.pt")
        else:
            stale += 1
            if stale >= args.patience:
                break
    report = {"task": task, "architecture": architecture, "model_version": f"arcade-instance-{architecture}-{args.run_id}",
              "category_ids": TASK_CATEGORY[task], "categories": {str(k): train.categories[k] for k in TASK_CATEGORY[task]},
              "input_size": args.input_size, "training_images": len(train), "validation_images": len(val),
              "training_duplicates_excluded_against_validation": train.excluded_train_duplicates,
              "best_validation": best_metrics, "primary_checkpoint_selection": "ARCADE official task mean F1 on full validation split",
              "official_evaluator_reference": {"tasks": "https://arcade.grand-challenge.org/tasks/",
                "syntax": "https://github.com/cmctec/ARCADE/blob/main/evaluation/evaluate_segmentation.py",
                "stenosis": "https://github.com/cmctec/ARCADE/blob/main/evaluation/evaluate_stenosis.py"},
              "evaluation_implementation": "Local port of the public polygon-area task rules; should be cross-checked against official evaluator before challenge submission.",
              "test_used_for_training_or_selection": False, "history": history, "run_id": args.run_id,
              "score_threshold": args.score_threshold, "clinical_validation": False}
    (out_dir / "report.json").write_text(json.dumps(report, indent=2))
    return report


def evaluate_candidate_test(args, device):
    """One final test-only pass using a candidate selected on validation."""
    candidate = json.loads((args.output_root / "candidate.json").read_text())
    architecture = candidate["architecture"]
    reports = {}
    available_tasks = candidate.get("tasks", {})
    tasks = tuple(task for task in ("syntax", "stenosis") if task in available_tasks)
    if args.task != "both":
        tasks = tuple(task for task in tasks if task == args.task)
    if not tasks:
        raise ValueError("No selected task exists in the validation-ranked candidate")
    result_path = args.output_root / "test_report.json"
    if result_path.exists():
        raise FileExistsError("Final test report already exists; do not repeatedly tune against test results")
    for task in tasks:
        checkpoint_path = args.output_root / task / architecture / "best.pt"
        if not checkpoint_path.is_file():
            raise FileNotFoundError(checkpoint_path)
    for task in tasks:
        checkpoint_path = args.output_root / task / architecture / "best.pt"
        checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
        model = build_detector(architecture, int(checkpoint["num_classes"]), pretrained=False).to(device)
        model.load_state_dict(checkpoint["state_dict"])
        test = ArcadeInstances(task, "test", int(checkpoint["input_size"]))
        metrics = evaluate(model, test, device, candidate.get("score_threshold", args.score_threshold),
                           candidate.get("pixel_threshold", args.pixel_threshold))
        reports[task] = {"test_images": len(test), "metrics": metrics}
    final = {"architecture": architecture, "run_id": candidate["run_id"],
             "selection_source": "official ARCADE validation split",
             "test_split_used_for_training_or_selection": False,
             "final_test_results": reports, "clinical_validation": False}
    result_path.write_text(json.dumps(final, indent=2))
    print(json.dumps(final, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=("syntax", "stenosis", "both"), default="both")
    parser.add_argument("--architectures", nargs="+", choices=("maskrcnn_resnet50_fpn", "maskrcnn_resnet50_fpn_v2"),
                        default=("maskrcnn_resnet50_fpn", "maskrcnn_resnet50_fpn_v2"))
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--input-size", type=int, default=512)
    parser.add_argument("--lr", type=float, default=0.002)
    parser.add_argument("--patience", type=int, default=6)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--score-threshold", type=float, default=0.25)
    parser.add_argument("--pixel-threshold", type=float, default=0.5)
    parser.add_argument("--val-limit", type=int, default=0, help="Debug only; 0 means full validation and official score")
    parser.add_argument("--evaluate-test-only", action="store_true",
                        help="Evaluate the validation-selected candidate in --output-dir once")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="Experiment directory (default: models/arcade_instances/experiments/<run-id>)")
    args = parser.parse_args()
    if args.epochs < 1 or args.batch_size < 1 or args.input_size < 128 or args.patience < 1:
        parser.error("epochs, batch-size, patience must be positive and input-size at least 128")
    args.output_root = args.output_dir or (ROOT / "models" / "arcade_instances" / "experiments" / args.run_id)
    if not args.output_root.is_absolute():
        args.output_root = ROOT / args.output_root
    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
    torch.set_num_threads(min(4, torch.get_num_threads()))
    device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"device={device}; test_split={'test-only final evaluation' if args.evaluate_test_only else 'not loaded'}", flush=True)
    if args.evaluate_test_only:
        evaluate_candidate_test(args, device)
        return
    tasks = ("syntax", "stenosis") if args.task == "both" else (args.task,)
    reports = [train_one(task, architecture, args, device)
               for task in tasks for architecture in args.architectures]
    comparison = {"run_id": args.run_id, "experiments": reports,
                  "selection_metric": "ARCADE official task mean F1 on validation; test excluded",
                  "test_used_for_training_or_selection": False, "clinical_validation": False}
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "comparison_report.json").write_text(json.dumps(comparison, indent=2))
    means = {}
    for arch in args.architectures:
        rows = [r for r in reports if r["architecture"] == arch]
        if rows and all(r["best_validation"].get("arcade_official_f1") is not None for r in rows):
            means[arch] = float(np.mean([r["best_validation"]["arcade_official_f1"] for r in rows]))
    if means:
        winner = max(means, key=means.get)
        candidate = {"architecture": winner, "run_id": args.run_id,
                    "version": f"arcade-instance-{winner}-{args.run_id}",
                    "input_size": args.input_size, "score_threshold": args.score_threshold,
                    "selection_metric": "mean syntax and stenosis ARCADE official validation F1",
                    "validation_official_f1_by_architecture": means,
                    "tasks": {r["task"]: {"checkpoint": f"{r['task']}/{winner}/best.pt",
                                             "validation": r["best_validation"]}
                              for r in reports if r["architecture"] == winner},
                    "test_used_for_training_or_selection": False, "clinical_validation": False}
        (args.output_root / "candidate.json").write_text(json.dumps(candidate, indent=2))
        print("Validation-ranked candidate (not promoted):", winner, means, flush=True)


if __name__ == "__main__":
    main()
