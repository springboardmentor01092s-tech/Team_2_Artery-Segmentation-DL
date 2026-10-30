"""Research-only inference for the two trained ARCADE binary masks."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .analysis_model import (analyze_vessel_geometry, build_model, centerline_overlay_png,
                             heatmap_overlay_png, overlay_png, postprocess_mask, prepare_input)
from .pixel_mlp import predict as predict_mlp
from . import trained_release

ROOT = Path(__file__).resolve().parents[2]
WEIGHTS = ROOT / "models" / "baseline"
INSTANCE_MODELS = ROOT / "models" / "arcade_instances"


def _instance_selection() -> dict:
    path = INSTANCE_MODELS / "promoted_model.json"
    try:
        selected = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    architecture = selected.get("architecture")
    tasks = selected.get("tasks", {})
    if architecture not in {"maskrcnn_resnet50_fpn", "maskrcnn_resnet50_fpn_v2"}:
        return {}
    if not all((INSTANCE_MODELS / task / architecture / "best.pt").is_file()
               for task in ("syntax", "stenosis")):
        return {}
    return selected

def model_version() -> str:
    if trained_release.configured():
        return trained_release.RELEASE['version']
    instance = _instance_selection()
    if instance:
        return instance.get("version", f"arcade-instance-{instance['architecture']}-{instance.get('run_id', 'v1')}")
    promoted = ROOT / "models" / "segmentation" / "promoted_model.json"
    if promoted.is_file():
        try:
            return json.loads(promoted.read_text()).get("version", "arcade-pixel-mlp-v2")
        except (OSError, ValueError):
            pass
    if all((WEIGHTS / f"{task}.pt").is_file() for task in ("syntax", "stenosis")):
        return "arcade-tiny-unet-v1"
    return "arcade-pixel-mlp-v2"


def selected_input_size() -> int:
    if trained_release.configured():
        return 512
    instance = _instance_selection()
    if instance:
        try:
            return int(instance.get("input_size", 512))
        except (TypeError, ValueError):
            return 512
    selected = ROOT / "models" / "segmentation" / "promoted_model.json"
    if selected.is_file():
        try:
            value = int(json.loads(selected.read_text()).get("input_size", 128))
            if 128 <= value <= 512 and value % 32 == 0:
                return value
        except (OSError, ValueError, TypeError):
            pass
    return 128


def models_ready() -> bool:
    if trained_release.configured():
        return trained_release.ready()
    if _instance_selection():
        return True
    selected_path = ROOT / "models" / "segmentation" / "promoted_model.json"
    if selected_path.is_file():
        try:
            architecture = json.loads(selected_path.read_text()).get("architecture")
            if architecture in {"tiny_unet", "attention_unet"} and all(
                    (ROOT / "models" / "segmentation" / task / f"{architecture}.pt").is_file()
                    for task in ("syntax", "stenosis")):
                return True
        except (OSError, ValueError):
            pass
    return any(all((WEIGHTS / f"{task}.{suffix}").is_file() for task in ("syntax", "stenosis"))
               for suffix in ("pt", "npz"))


@lru_cache(maxsize=2)
def _model(task: str):
    import torch

    if task not in {"syntax", "stenosis"}:
        raise ValueError("Invalid analysis task")
    model = build_model()
    model.load_state_dict(torch.load(WEIGHTS / f"{task}.pt", map_location="cpu", weights_only=True))
    model.eval()
    return model


def _gradcam(model, image, threshold: float):
    """Grad-CAM for the segmentation logit target; this is a saliency map, not a diagnosis."""
    import torch
    import torch.nn.functional as F

    layer = getattr(model, "bridge", getattr(model, "middle", None))
    if layer is None:
        return None
    capture = {}

    def save_activation(_module, _inputs, output):
        capture["activation"] = output
        output.register_hook(lambda gradient: capture.__setitem__("gradient", gradient))

    handle = layer.register_forward_hook(save_activation)
    try:
        model.zero_grad(set_to_none=True)
        with torch.enable_grad():
            logits = model(image.detach().clone().requires_grad_(True))
            selected = logits.detach().sigmoid() >= float(threshold)
            target = logits[selected].mean() if bool(selected.any()) else logits.max()
            target.backward()
        activation, gradient = capture.get("activation"), capture.get("gradient")
        if activation is None or gradient is None:
            return None
        weights = gradient.mean(dim=(2, 3), keepdim=True)
        cam = torch.relu((weights * activation).sum(dim=1, keepdim=True))
        # Preserve the exact model-input frame. A hard-coded output size would
        # misregister the saved attribution whenever a selected model does not
        # use the legacy 128-square contract.
        cam = F.interpolate(cam, size=tuple(image.shape[-2:]), mode="bilinear",
                            align_corners=False)[0, 0]
        cam = cam - cam.min()
        cam = cam / cam.max().clamp_min(1e-8)
        return cam.detach().cpu().numpy()
    finally:
        handle.remove()
        model.zero_grad(set_to_none=True)


def _threshold_sensitivity(probabilities, selected_mask, threshold: float,
                           spacing_mm: tuple[float, float] | None) -> dict:
    import numpy as np

    if probabilities is None:
        return {"status": "unavailable", "reference_threshold": threshold, "evaluations": []}
    from .analysis_model import postprocess_mask

    thresholds = sorted({round(float(max(0, threshold - 0.1)), 3), round(float(threshold), 3),
                         round(float(min(1, threshold + 0.1)), 3)})
    evaluations = []
    for value in thresholds:
        candidate = postprocess_mask(probabilities >= value)
        intersection = int(np.count_nonzero(candidate & selected_mask))
        dice = 2 * intersection / max(int(candidate.sum()) + int(selected_mask.sum()), 1)
        geometry = analyze_vessel_geometry(candidate, spacing_mm, probabilities, value)
        evaluations.append({"threshold": value, "mask_dice_vs_selected": round(dice, 4),
                            "connected_components": geometry["connected_components"],
                            "centerline_length": geometry["centerline_length"],
                            "branch_points": geometry["branching_points"],
                            "endpoints": geometry["endpoints"],
                            "path_count": len(geometry["centerline_paths"])})
    alternatives = [row for row in evaluations if row["threshold"] != round(threshold, 3)]
    stable = all(row["mask_dice_vs_selected"] >= 0.8 for row in alternatives)
    return {"reference_threshold": round(threshold, 3), "status": "threshold_stable" if stable else "threshold_sensitive",
            "stability_rule": "alternate-mask Dice >= 0.80 at threshold offsets up to 0.10",
            "evaluations": evaluations}


def analyze(preview_path: Path, spacing_mm: tuple[float, float] | None = None) -> tuple[bytes, int, int, dict, bytes | None, bytes | None, bytes | None, bytes | None, dict, bytes]:
    if trained_release.configured():
        return trained_release.analyze(preview_path, spacing_mm)
    if not models_ready():
        raise FileNotFoundError("Train both ARCADE models before running analysis")
    selected = _instance_selection()
    if not selected:
        advanced_selection = ROOT / "models" / "segmentation" / "promoted_model.json"
        if advanced_selection.is_file():
            try:
                selected = json.loads(advanced_selection.read_text())
            except (OSError, ValueError):
                selected = {}
    if selected.get("architecture") in {"maskrcnn_resnet50_fpn", "maskrcnn_resnet50_fpn_v2"}:
        import numpy as np
        import torch
        import torch.nn.functional as F
        from PIL import Image

        torch.set_num_threads(min(4, torch.get_num_threads()))
        input_size = int(selected.get("input_size", 512))
        score_threshold = float(selected.get("score_threshold", 0.25))
        with Image.open(preview_path) as opened:
            source = opened.convert("RGB").resize((input_size, input_size), Image.Resampling.BILINEAR)
        image = torch.from_numpy(np.asarray(source, dtype=np.float32).copy() / 255.0).permute(2, 0, 1)
        predictions, probability_maps, instance_detections = {}, {}, []
        for task in ("syntax", "stenosis"):
            checkpoint = INSTANCE_MODELS / task / selected["architecture"] / "best.pt"
            model = _instance_model(task, selected["architecture"], checkpoint)
            with torch.inference_mode():
                output = model([image])[0]
            union_mask = np.zeros((input_size, input_size), dtype=bool)
            probability = np.zeros((input_size, input_size), dtype=np.float32)
            for index, confidence in enumerate(output["scores"].cpu().numpy()):
                category_id = int(output["labels"][index].item())
                if confidence < score_threshold:
                    continue
                if task == "stenosis" and category_id != 1:
                    continue
                mask_probability = output["masks"][index, 0].cpu().numpy()
                instance_mask = mask_probability >= 0.5
                if not instance_mask.any():
                    continue
                union_mask |= instance_mask
                probability = np.maximum(probability, mask_probability * float(confidence))
                instance_detections.append({"task": task, "category_id": 26 if task == "stenosis" else category_id,
                                            "model_score": round(float(confidence), 4),
                                            "mask_pixels": int(instance_mask.sum()),
                                            "calibration": "uncalibrated_detection_score"})
            predictions[task] = postprocess_mask(union_mask)
            probability_maps[task] = probability
        artery, stenosis = predictions["syntax"], predictions["stenosis"]
        artery_probability_map = probability_maps["syntax"]
        artery_threshold = 0.5
        probability_png = heatmap_overlay_png(preview_path, probability_maps["stenosis"])
        artery_probability_png = heatmap_overlay_png(preview_path, artery_probability_map)
        attention_png, gradcam_png = None, None
        scores = {"artery_foreground_mean_probability": round(float(artery_probability_map[artery].mean()), 4) if artery.any() else None,
                  "stenosis_foreground_mean_probability": round(float(probability_maps["stenosis"][stenosis].mean()), 4) if stenosis.any() else None,
                  "calibration": "uncalibrated_mask_times_detection_scores",
                  "instance_detections": instance_detections}
        scores["explainability"] = {
            "gradcam": {"status": "unavailable", "reason": "Mask R-CNN adapter has no verified attribution target/layer contract."},
            "attention": {"status": "unavailable", "reason": "This architecture does not expose attention-gate maps."},
        }
    elif selected.get("architecture") in {"tiny_unet", "attention_unet"}:
        import torch

        torch.set_num_threads(min(4, torch.get_num_threads()))
        input_size = selected_input_size()
        image = torch.from_numpy(prepare_input(preview_path, input_size))[None]
        predictions, probability_maps = {}, {}
        attention_map, gradcam_map = None, None
        for task in ("syntax", "stenosis"):
            checkpoint = ROOT / "models" / "segmentation" / task / f"{selected['architecture']}.pt"
            model = _segmentation_model(task, selected["architecture"], checkpoint)
            with torch.inference_mode():
                threshold = float(selected.get("thresholds", {}).get(task, 0.5))
                probabilities = model(image).sigmoid()[0, 0].cpu().numpy()
                probability_maps[task] = probabilities
                predictions[task] = postprocess_mask(probabilities >= threshold)
                if task == "stenosis" and selected["architecture"] == "attention_unet":
                    import torch.nn.functional as F
                    gate1 = model.att1.last_attention_map
                    gate2 = model.att2.last_attention_map
                    attention_map = (gate1 + F.interpolate(gate2, size=gate1.shape[-2:], mode="bilinear",
                                                            align_corners=False)) / 2
                    attention_map = attention_map[0, 0].cpu().numpy()
            try:
                gradcam_map = _gradcam(model, image, threshold) if task == "stenosis" else gradcam_map
            except (RuntimeError, AttributeError):
                gradcam_map = None
        artery, stenosis = predictions["syntax"], predictions["stenosis"]
        artery_probability_map = probability_maps["syntax"]
        artery_threshold = float(selected.get("thresholds", {}).get("syntax", 0.5))
        scores = {
            "artery_foreground_mean_probability": round(float(probability_maps["syntax"][artery].mean()), 4) if artery.any() else None,
            "stenosis_foreground_mean_probability": round(float(probability_maps["stenosis"][stenosis].mean()), 4) if stenosis.any() else None,
            "calibration": "uncalibrated_pixel_probabilities",
        }
        probability_png = heatmap_overlay_png(preview_path, probability_maps["stenosis"])
        artery_probability_png = heatmap_overlay_png(preview_path, probability_maps["syntax"])
        attention_png = heatmap_overlay_png(preview_path, attention_map, "attention") if attention_map is not None else None
        gradcam_png = heatmap_overlay_png(preview_path, gradcam_map, "attention") if gradcam_map is not None else None
        scores["explainability"] = {
            "gradcam": ({"status": "saved", "method": "gradcam_v1",
                         "target": "mean selected stenosis logits, or maximum logit when no pixel is selected",
                         "layer": "bridge" if hasattr(model, "bridge") else "middle",
                         "coordinate_frame": f"model_input_{input_size}x{input_size}",
                         "mapping": "bilinear activation-map upsampling to the exact model-input frame",
                         "weights_updated": False, "clinical_validated": False}
                        if gradcam_map is not None else
                        {"status": "unavailable", "reason": "Compatible activation/gradient capture was not produced."}),
            "attention": ({"status": "saved", "method": "attention_gate_average_v1",
                           "coordinate_frame": f"model_input_{input_size}x{input_size}",
                           "faithfulness_validated": False, "clinical_validated": False}
                          if attention_map is not None else
                          {"status": "unavailable", "reason": "Selected architecture has no saved attention-gate map."}),
        }
    elif model_version() == "arcade-tiny-unet-v1":
        import torch

        torch.set_num_threads(min(4, torch.get_num_threads()))
        image = torch.from_numpy(prepare_input(preview_path))[None]
        with torch.inference_mode():
            artery_threshold = 0.5
            artery_probability = _model("syntax")(image).sigmoid()[0, 0].numpy()
            stenosis_model = _model("stenosis")
            stenosis_probability = stenosis_model(image).sigmoid()[0, 0].numpy()
            artery = postprocess_mask(artery_probability >= 0.5)
            stenosis = postprocess_mask(stenosis_probability >= 0.5)
        artery_probability_map = artery_probability
        try:
            gradcam_map = _gradcam(stenosis_model, image, 0.5)
        except (RuntimeError, AttributeError):
            gradcam_map = None
        probability_png = heatmap_overlay_png(preview_path, stenosis_probability)
        artery_probability_png = heatmap_overlay_png(preview_path, artery_probability)
        attention_png = None
        gradcam_png = heatmap_overlay_png(preview_path, gradcam_map, "attention") if gradcam_map is not None else None
        scores = {
            "artery_foreground_mean_probability": None,
            "stenosis_foreground_mean_probability": None,
            "calibration": "unavailable_for_legacy_model",
            "explainability": {
                "gradcam": ({"status": "saved", "method": "gradcam_v1",
                             "target": "mean selected stenosis logits, or maximum logit when no pixel is selected",
                             "layer": "middle", "coordinate_frame": "model_input_128x128",
                             "mapping": "bilinear activation-map upsampling to the exact model-input frame",
                             "weights_updated": False, "clinical_validated": False}
                            if gradcam_map is not None else
                            {"status": "unavailable", "reason": "Compatible activation/gradient capture was not produced."}),
                "attention": {"status": "unavailable", "reason": "Legacy model has no attention-gate map."},
            },
        }
    else:
        artery_probability_map = None
        artery_threshold = 0.5
        artery = predict_mlp(preview_path, WEIGHTS / "syntax.npz")
        stenosis = predict_mlp(preview_path, WEIGHTS / "stenosis.npz")
        probability_png, artery_probability_png, attention_png, gradcam_png = None, None, None, None
        scores = {"artery_foreground_mean_probability": None,
                  "stenosis_foreground_mean_probability": None,
                  "calibration": "unavailable_for_pixel_model",
                  "explainability": {
                      "gradcam": {"status": "unavailable", "reason": "Pixel model has no convolutional attribution target."},
                      "attention": {"status": "unavailable", "reason": "Pixel model has no attention-gate map."},
                  }}
    from scipy import ndimage
    stenosis_components = int(ndimage.label(stenosis)[1])
    input_size = selected_input_size() if selected.get("architecture") in {
        "tiny_unet", "attention_unet", "maskrcnn_resnet50_fpn", "maskrcnn_resnet50_fpn_v2"} else 128
    model_spacing = tuple(value * (512 / input_size) for value in spacing_mm) if spacing_mm else None
    vessel = analyze_vessel_geometry(artery, model_spacing, artery_probability_map, artery_threshold)
    stability = _threshold_sensitivity(artery_probability_map, artery, artery_threshold, model_spacing)
    vessel["threshold_sensitivity"] = stability
    vessel["stenosis_mask_components"] = stenosis_components
    vessel["stenosis_component_interpretation"] = "Disconnected predicted mask components; not a confirmed lesion count."
    if stability["status"] == "threshold_sensitive":
        vessel["quality_flags"].append({"code": "threshold_sensitive_centerline", "severity": "review",
                                        "message": "Small changes to the artery threshold substantially change the predicted mask; inspect alternate-threshold results."})
        vessel["quality_status"] = "review_required"
    centerline_png = centerline_overlay_png(preview_path, vessel["centerline_paths"],
                                             vessel["branch_points"], vessel["endpoint_points"], artery,
                                             input_size)
    return (overlay_png(preview_path, artery, stenosis), int(artery.sum()), int(stenosis.sum()), vessel,
            attention_png, artery_probability_png, probability_png, gradcam_png, scores, centerline_png)


@lru_cache(maxsize=4)
def _segmentation_model(task: str, architecture: str, checkpoint: Path):
    import torch
    from .analysis_model import build_attention_unet

    if task not in {"syntax", "stenosis"} or architecture not in {"tiny_unet", "attention_unet"}:
        raise ValueError("Invalid segmentation model")
    model = build_attention_unet() if architecture == "attention_unet" else build_model()
    model.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=True))
    model.eval()
    return model


@lru_cache(maxsize=2)
def _instance_model(task: str, architecture: str, checkpoint: Path):
    """Load one category-aware Mask R-CNN checkpoint for online inference."""
    import torch
    from torchvision.models.detection import maskrcnn_resnet50_fpn, maskrcnn_resnet50_fpn_v2
    from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
    from torchvision.models.detection.mask_rcnn import MaskRCNNPredictor

    payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
    if task not in {"syntax", "stenosis"} or architecture not in {
            "maskrcnn_resnet50_fpn", "maskrcnn_resnet50_fpn_v2"}:
        raise ValueError("Invalid instance segmentation model")
    model = (maskrcnn_resnet50_fpn_v2(weights=None) if architecture == "maskrcnn_resnet50_fpn_v2"
             else maskrcnn_resnet50_fpn(weights=None))
    num_classes = int(payload["num_classes"])
    box_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(box_features, num_classes)
    mask_features = model.roi_heads.mask_predictor.conv5_mask.in_channels
    model.roi_heads.mask_predictor = MaskRCNNPredictor(mask_features, 256, num_classes)
    model.load_state_dict(payload["state_dict"])
    model.eval()
    return model


def validation_summary() -> dict:
    if trained_release.configured():
        return {item['task']: {k: item[k] for k in ('validation_dice', 'validation_images', 'validation_iou', 'validation_status')}
                for item in trained_release.RELEASE['models']}
    selection_path = ROOT / "models" / "segmentation" / "promoted_model.json"
    if selection_path.is_file():
        try:
            selected = json.loads(selection_path.read_text())
            architecture = selected["architecture"]
            report_path = ROOT / "models" / "segmentation" / "comparison_report.json"
            comparison = json.loads(report_path.read_text())
            rows = [row for row in comparison.get("experiments", []) if row["architecture"] == architecture]
            if rows:
                return {row["task"]: {"validation_dice": row["best_validation"]["dice"],
                                      "mean_image_pixel_f1": row["best_validation"].get("mean_image_pixel_f1"),
                                      "selection_score": row["best_validation"].get("selection_score"),
                                      "validation_images": row["validation_images"],
                                      "validation_iou": row["best_validation"]["iou"],
                                      "architecture": architecture}
                        for row in rows}
        except (OSError, ValueError, KeyError, TypeError):
            pass
    path = WEIGHTS / ("training_report.json" if model_version() == "arcade-tiny-unet-v1"
                      else "training_report_mlp.json")
    if not path.is_file():
        return {}
    return {row["task"]: {"validation_dice": row["best_validation_dice"],
                           "validation_images": row["validation_images"]}
            for row in json.loads(path.read_text())}
