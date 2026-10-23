"""Versioned research result and deterministic explanations from saved evidence.

No image diagnosis, language-model call, severity threshold or confidence fitting.
"""
import json
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class Stage(BaseModel):
    status: Literal["completed", "review_required", "skipped", "blocked"]
    reason: str


class ResearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["corovision.result.v1"] = "corovision.result.v1"
    result_id: str
    job_id: str | None
    case_id: str
    asset_id: str
    created_at: str
    model_version: str
    models: dict
    input: dict
    coordinates: dict
    artifacts: dict
    stages: dict[str, Stage]
    measurements: dict
    candidates: list[dict]
    severity: dict
    validation_evidence: dict
    quality: dict
    limitations: list[str]
    review_status: Literal["pending_human_review"] = "pending_human_review"
    explanation: dict = Field(default_factory=dict)


def candidate_coordinates(candidate, geometry, width, height):
    """Map mask-derived prepared bounds to source pixel edges, preserving padding flags."""
    row = dict(candidate)
    row["vessel_segment_id"] = None
    row["association_status"] = "not_assessed"
    box = row.get("bbox_prepared_xyxy")
    row["bbox_source_xyxy"] = None
    row["coordinate_warning"] = None
    if not box or not geometry:
        row["coordinate_warning"] = "Source mapping unavailable; prepared coordinates only."
        return row
    left, top = geometry["padding_left_top_xy"]
    cw, ch = geometry["content_size_xy"]
    sx, sy = geometry["source_pixels_per_content_pixel_xy"]
    ox, oy = geometry["source_roi_origin_xy"]
    x1, y1, x2, y2 = box
    if x1 < left or y1 < top or x2 > left + cw or y2 > top + ch:
        row["coordinate_warning"] = "Candidate intersects padding; source bounds are clipped to valid content."
    x1, x2 = max(left, min(left + cw, x1)), max(left, min(left + cw, x2))
    y1, y2 = max(top, min(top + ch, y1)), max(top, min(top + ch, y2))
    if x2 <= x1 or y2 <= y1:
        row["coordinate_warning"] = "Candidate is outside source content; no source location is asserted."
        return row
    row["bbox_source_xyxy"] = [max(0., min(float(width), ox + (x1-left)*sx)),
                                max(0., min(float(height), oy + (y1-top)*sy)),
                                max(0., min(float(width), ox + (x2-left)*sx)),
                                max(0., min(float(height), oy + (y2-top)*sy))]
    return row


def explain(result):
    """References are paths into this exact result; numbers remain authoritative there."""
    stages = result["stages"]
    measurements = result["measurements"]
    sections = [
        dict(title="Analysis summary", source_refs=["model_version", "stages", "input"],
             text=f"Research analysis with {result['model_version']}. " +
             " ".join(f"{name.replace('_', ' ')}: {stage['status'].replace('_', ' ')}." for name, stage in stages.items())),
        dict(title="Artery segmentation", source_refs=["measurements.artery_pixels", "artifacts", "quality"],
             text=f"The model predicted {measurements['artery_pixels']} artery-mask pixels in the prepared image. "
                  "The mask requires image review; prediction alone does not establish anatomical correctness."),
        dict(title="Vessel structure", source_refs=["measurements.vessel_analysis", "stages.vessel_analysis"],
             text=("Vessel analysis was skipped because the artery mask is empty." if stages["vessel_analysis"]["status"] == "skipped" else
                   "Centerlines and diameter/length estimates derive from the predicted 2D mask. "
                   "Use the recorded units; projection and segmentation errors affect these estimates.")),
        dict(title="Stenosis candidates", source_refs=["candidates", "measurements.stenosis_pixels"],
             text=(f"The mask model returned {len(result['candidates'])} candidate instance(s). "
                   "Scores are raw model outputs, not calibrated patient disease probabilities."
                   if result["candidates"] else
                   ("No candidate detected by this model. Missed regions remain possible; this does not establish a healthy case."
                    if measurements['stenosis_pixels'] == 0 else
                    "A stenosis mask was produced, but candidate-instance coordinates are unavailable for this adapter."))),
        dict(title="Severity assessment", source_refs=["severity"],
             text="Not assessed — insufficient evidence. A validated candidate-local diameter and reference-segment protocol is unavailable."),
        dict(title="Evidence and limitations", source_refs=["validation_evidence", "limitations", "review_status"],
             text="Validation metrics describe their recorded dataset/split and aggregation, not accuracy on this image. "
                  "A human assessment is separate from these model and algorithm outputs. " + " ".join(result["limitations"])),
    ]
    return dict(version="corovision.explanation.v1", method="deterministic_saved_result_template", sections=sections)


def build_result(*, event_id, job_id, image, case, version, scores, vessel, artery_pixels,
                 stenosis_pixels, evidence, artifacts, timestamp):
    # Pydantic JSON mode can convert non-finite floats to null; reject them first.
    json.dumps(dict(scores=scores, vessel=vessel, evidence=evidence), allow_nan=False)
    config = json.loads(image.preprocessing_config_json or "{}")
    geometry = config.get("resize_geometry")
    candidates = [candidate_coordinates(row, geometry, image.width, image.height)
                  for row in scores.get("instance_detections", [])]
    for index, row in enumerate(candidates):
        row.setdefault("candidate_id", f"C{index+1}")
    flags = vessel.get("quality_flags", [])
    limitations = ["Research output; not a standalone diagnosis.",
                   "Raw scores are not calibrated patient confidence.",
                   "No detections do not establish absence of disease.",
                   "No validated automatic severity or vessel-segment association.",
                   "2D projection and preprocessing can change measurement reliability."]
    if image.width != 512 or image.height != 512 or config.get("roi_box_xyxy"):
        limitations.append("Resizing, ROI or padding differs from the verified 512-square development parity input.")
    if config.get("source_format") not in (None, "image/png") or any(config.get("options", {}).values()):
        limitations.append("Source rendering or optional preprocessing is outside the verified baseline PNG parity example.")
    result = ResearchResult(
        result_id=event_id, job_id=job_id, case_id=case.id, asset_id=image.id,
        created_at=timestamp, model_version=version,
        models=dict(checkpoint_sha256=scores.get("checkpoint_sha256", {}),
                    approval_scope="preserved_research_baseline" if scores.get("trained_release") else "legacy_research_provider"),
        input=dict(modality=config.get("modality", case.modality), modality_source="operator_declared",
                   anatomy=case.anatomy, source_sha256=image.source_sha256,
                   prepared_sha256=image.processed_sha256, preprocessing=config),
        coordinates=dict(prediction_frame="prepared_512_xy", source_size_xy=[image.width, image.height],
                         prepared_size_xy=[512, 512], source_mapping=geometry,
                         bbox_convention="pixel_edges_xyxy_half_open", volume=False),
        artifacts=artifacts,
        stages={"preprocessing": Stage(status="completed", reason="Saved upload processing record used."),
                "artery_segmentation": Stage(status="review_required", reason="Model-generated mask; anatomical correctness requires review."),
                "vessel_analysis": Stage(status="review_required" if artery_pixels else "skipped",
                                         reason="Mask-derived 2D estimates." if artery_pixels else "No artery pixels; no meaningful geometry."),
                "stenosis_detection": Stage(status="review_required", reason="Compatible image model; candidates are not diagnoses. Vessel association not assessed."),
                "severity_assessment": Stage(status="blocked", reason="Validated local/reference diameter protocol unavailable.")},
        measurements=dict(artery_pixels=artery_pixels, stenosis_pixels=stenosis_pixels,
                          pixel_count_frame="prepared_512", vessel_analysis=vessel if artery_pixels else None),
        candidates=candidates,
        severity=dict(status="insufficient_evidence", reference_diameter=None, minimum_diameter=None,
                      diameter_unit=None, narrowing_percent=None, category=None, reference_selection=None,
                      reason="No validated candidate-local/reference-vessel measurement protocol or category standard."),
        validation_evidence=evidence, quality=dict(status="review_required", flags=flags), limitations=limitations,
    ).model_dump(mode="json")
    result["explanation"] = explain(result)
    # Reject NaN/Infinity and non-serializable values before writing any result metadata.
    json.dumps(result, allow_nan=False)
    return ResearchResult.model_validate(result).model_dump(mode="json")
