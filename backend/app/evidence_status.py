"""Saved metadata availability; no image decoding or inference."""
import json


def saved_analysis_metadata(raw):
    """Malformed legacy metadata stays unknown, rather than becoming a negative."""
    try:
        details = json.loads(raw or "{}")
    except (TypeError, ValueError):
        return None, {}
    if not isinstance(details, dict):
        return None, {}
    vessel = details.get("vessel_analysis")
    return details, vessel if isinstance(vessel, dict) else {}


def stenosis_mask_status(details):
    if not isinstance(details, dict):
        return "unknown"
    structured = details.get("structured_result") or {}
    stages = structured.get("stages") or {} if isinstance(structured, dict) else {}
    stage = stages.get("stenosis_detection") or {} if isinstance(stages, dict) else {}
    if isinstance(stage, dict) and stage.get("status") == "skipped":
        return "not_assessed"
    scores = details.get("model_scores") or {}
    if isinstance(scores, dict) and scores.get("pixel_counts_unavailable") is True:
        return "not_saved"
    return "recorded"
