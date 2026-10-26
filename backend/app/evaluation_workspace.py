"""Authenticated experiment imports and research review, isolated from inference promotion."""
import base64
import io
import json
import os
from datetime import timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

import numpy as np
from PIL import Image
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .database import BASE_DIR, get_db
from .models import AuditEvent, EvaluationDecision, EvaluationExperiment, EvaluationPolicy, EvaluationSampleReview, User
from .security import current_user

router = APIRouter(prefix="/api/evaluation/workspace", tags=["Evaluation workspace"])


def readers(user: User = Depends(current_user)):
    if user.role not in {"admin", "researcher", "ml_engineer"}:
        raise HTTPException(403, "Evaluation workspace requires a research or model-management role")
    return user


def writers(user: User = Depends(readers)):
    if user.role not in {"admin", "ml_engineer"}:
        raise HTTPException(403, "Only administrators and ML engineers may import experiments")
    return user


def admins(user: User = Depends(readers)):
    if user.role != "admin":
        raise HTTPException(403, "Research approval requires administrator review")
    return user


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Metric(StrictModel):
    name: str = Field(min_length=1, max_length=80)
    value: FiniteFloat | None = None
    unit: str = Field(min_length=1, max_length=40)
    definition: str = Field(min_length=1, max_length=1000)
    aggregation: str = Field(min_length=1, max_length=100)
    higher_is_better: bool = True

    @model_validator(mode="after")
    def ratio_range(self):
        if self.unit == "ratio" and self.value is not None and not 0 <= self.value <= 1:
            raise ValueError("Ratio metrics must be between zero and one")
        return self


class Epoch(StrictModel):
    epoch: int = Field(ge=0)
    values: dict[str, FiniteFloat | None] = Field(max_length=30)


class Dataset(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    version: str = Field(min_length=1, max_length=120)
    split: Literal["training", "validation", "test", "independent_test"]
    protocol: str = Field(min_length=1, max_length=500)
    counts: dict[str, int] = Field(default_factory=dict, max_length=20)
    annotation_types: dict[str, int] = Field(default_factory=dict, max_length=20)
    class_counts: dict[str, int] = Field(default_factory=dict, max_length=100)
    foreground_prevalence: FiniteFloat | None = Field(default=None, ge=0, le=1)
    patient_independence_verified: bool | None = None
    audit_notes: str = Field(default="", max_length=4000)
    exclusions: dict[str, int] = Field(default_factory=dict, max_length=50)

    @model_validator(mode="after")
    def positive_counts(self):
        if any(value < 0 for group in (self.counts, self.annotation_types, self.class_counts, self.exclusions) for value in group.values()):
            raise ValueError("Dataset counts cannot be negative")
        return self


class Sample(StrictModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9_.-]{1,100}$")
    metrics: list[Metric] = Field(default_factory=list, max_length=30)
    error_category: str | None = Field(default=None, max_length=120)
    notes: str = Field(default="", max_length=2000)
    reference_available: bool = False
    reviewed: bool = False
    artifacts: dict[str, str] = Field(default_factory=dict, max_length=6)
    spatial_metadata: dict = Field(default_factory=dict)


class Artifact(StrictModel):
    key: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")
    format: Literal["png", "npy"]
    data_base64: str = Field(max_length=12_000_000)


class Threshold(StrictModel):
    metric: str = Field(min_length=1, max_length=80)
    minimum: FiniteFloat | None = None
    maximum: FiniteFloat | None = None

    @model_validator(mode="after")
    def bounds(self):
        if self.minimum is None and self.maximum is None:
            raise ValueError("A threshold needs a minimum or maximum")
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("Minimum exceeds maximum")
        return self


class Policy(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    task: str = Field(min_length=1, max_length=120)
    dataset: Dataset
    thresholds: list[Threshold] = Field(min_length=1, max_length=30)
    review_requirements: str = Field(min_length=10, max_length=4000)


class Experiment(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    architecture: str = Field(min_length=1, max_length=120)
    version: str = Field(min_length=1, max_length=120)
    checkpoint_sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    task: str = Field(min_length=1, max_length=120)
    dimension: Literal["2D", "3D"]
    execution_status: Literal["completed", "failed"] = "completed"
    dataset: Dataset
    metrics: list[Metric] = Field(default_factory=list, max_length=40)
    epochs: list[Epoch] = Field(default_factory=list, max_length=5000)
    samples: list[Sample] = Field(default_factory=list, max_length=1000)
    artifacts: list[Artifact] = Field(default_factory=list, max_length=30)
    configuration: dict[str, str | int | float | bool | None] = Field(default_factory=dict, max_length=50)
    evaluated_at: str | None = Field(default=None, max_length=100)
    runtime_seconds: FiniteFloat | None = Field(default=None, ge=0)
    hardware: str | None = Field(default=None, max_length=200)
    code_revision: str | None = Field(default=None, max_length=120)
    seed: int | None = None
    best_epoch: int | None = Field(default=None, ge=0)
    early_stopping_epoch: int | None = Field(default=None, ge=0)
    failure_log: str = Field(default="", max_length=10000)
    policy_id: str | None = None
    curves: dict[str, list[list[FiniteFloat]]] = Field(default_factory=dict, max_length=10)
    confusion_matrix: list[list[int]] = Field(default_factory=list, max_length=30)
    class_labels: list[str] = Field(default_factory=list, max_length=30)
    deidentified_research_data: Literal[True]

    @model_validator(mode="after")
    def references(self):
        if len(json.dumps(self.configuration)) > 10000 or any(isinstance(v, float) and not np.isfinite(v) for v in self.configuration.values()):
            raise ValueError("Configuration must be bounded and finite")
        if len({m.name for m in self.metrics}) != len(self.metrics):
            raise ValueError("Metric names must be unique")
        if len({s.id for s in self.samples}) != len(self.samples):
            raise ValueError("Sample IDs must be unique")
        epochs = [e.epoch for e in self.epochs]
        if epochs != sorted(set(epochs)):
            raise ValueError("Epochs must be unique and increasing")
        if any(e is not None and e not in epochs for e in (self.best_epoch, self.early_stopping_epoch)):
            raise ValueError("Checkpoint epochs must occur in history")
        if len({a.key for a in self.artifacts}) != len(self.artifacts):
            raise ValueError("Artifact keys must be unique")
        keys = {a.key for a in self.artifacts}
        definitions = {}
        for sample in self.samples:
            for metric in sample.metrics:
                definition = (metric.unit, metric.definition, metric.aggregation)
                if metric.name in definitions and definitions[metric.name] != definition:
                    raise ValueError("Sample metric definitions must be consistent within an experiment")
                definitions[metric.name] = definition
            if set(sample.artifacts) - {"original", "reference", "prediction", "probability", "overlay", "difference"}:
                raise ValueError("Unsupported artifact layer")
            if set(sample.artifacts.values()) - keys:
                raise ValueError("Sample references an absent artifact")
            if self.dimension == "3D" and sample.artifacts and not all(k in sample.spatial_metadata for k in ("spacing", "affine", "coordinate_frame")):
                raise ValueError("3D artifacts require spacing, affine and coordinate frame")
            if self.dimension == "3D" and sample.artifacts:
                spacing = np.asarray(sample.spatial_metadata["spacing"], dtype=float)
                affine = np.asarray(sample.spatial_metadata["affine"], dtype=float)
                if spacing.shape != (3,) or not np.isfinite(spacing).all() or not (spacing > 0).all() or affine.shape != (4, 4) or not np.isfinite(affine).all() or not isinstance(sample.spatial_metadata["coordinate_frame"], str):
                    raise ValueError("Invalid 3D spatial metadata")
        if self.confusion_matrix and (len(self.confusion_matrix) != len(self.class_labels) or any(len(row) != len(self.class_labels) or any(v < 0 for v in row) for row in self.confusion_matrix)):
            raise ValueError("Confusion matrix must match labels and have nonnegative counts")
        for points in self.curves.values():
            if len(points) > 5000 or any(len(p) != 2 for p in points):
                raise ValueError("Curve points must be finite [x,y] pairs, at most 5000")
        return self


def get_run(db, run_id):
    row = db.get(EvaluationExperiment, run_id)
    if not row:
        raise HTTPException(404, "Experiment not found")
    return row


def output(row, db):
    result = json.loads(row.payload_json)
    result.update(id=row.id, status=row.status, imported_by=row.owner_id, imported_at=row.created_at.replace(tzinfo=timezone.utc).isoformat())
    result["decisions"] = [{"decision": d.decision, "reviewer_id": d.reviewer_id, "notes": d.notes, "created_at": d.created_at.replace(tzinfo=timezone.utc).isoformat()}
                           for d in db.scalars(select(EvaluationDecision).where(EvaluationDecision.experiment_id == row.id).order_by(EvaluationDecision.created_at))]
    result["sample_reviews"] = [{"sample_id": s.sample_id, "reviewer_id": s.reviewer_id, "notes": s.notes, "created_at": s.created_at.replace(tzinfo=timezone.utc).isoformat()}
                              for s in db.scalars(select(EvaluationSampleReview).where(EvaluationSampleReview.experiment_id == row.id).order_by(EvaluationSampleReview.created_at))]
    return result


def audit(db, user, action):
    db.add(AuditEvent(user_id=user.id, action=action))


@router.get("")
def list_runs(user: User = Depends(readers), db: Session = Depends(get_db)):
    return {"runs": [output(row, db) for row in db.scalars(select(EvaluationExperiment).order_by(EvaluationExperiment.created_at.desc()))],
            "can_import": user.role in {"admin", "ml_engineer"}, "can_review": user.role == "admin"}


@router.get("/schema")
def import_schema(user: User = Depends(readers)):
    return Experiment.model_json_schema()


@router.get("/policies")
def policies(user: User = Depends(readers), db: Session = Depends(get_db)):
    return [{"id": row.id, **json.loads(row.payload_json), "created_at": row.created_at.isoformat()}
            for row in db.scalars(select(EvaluationPolicy).order_by(EvaluationPolicy.created_at.desc()))]


@router.get("/policies/schema")
def policy_schema(user: User = Depends(admins)):
    return Policy.model_json_schema()


@router.post("/policies", status_code=201)
def create_policy(data: Policy, user: User = Depends(admins), db: Session = Depends(get_db)):
    row = EvaluationPolicy(owner_id=user.id, payload_json=data.model_dump_json())
    db.add(row); audit(db, user, "evaluation_policy_created"); db.commit()
    return {"id": row.id}


@router.post("", status_code=201)
def import_run(data: Experiment, user: User = Depends(writers), db: Session = Depends(get_db)):
    # Immutable imports: no baseline replacement, no arbitrary file paths or URLs.
    if len(data.model_dump_json()) > 40_000_000:
        raise HTTPException(413, "Experiment bundle exceeds 40 MB")
    if data.policy_id and not db.get(EvaluationPolicy, data.policy_id):
        raise HTTPException(422, "Unknown acceptance policy")
    stored = data.model_dump(exclude={"artifacts"})
    blobs = {}
    for artifact in data.artifacts:
        try:
            raw = base64.b64decode(artifact.data_base64, validate=True)
            if artifact.format == "png":
                with Image.open(io.BytesIO(raw)) as image:
                    if image.format != "PNG" or image.width * image.height > 4_194_304:
                        raise ValueError("PNG exceeds image bounds")
                    image.load()
                    array = np.asarray(image)
            else:
                array = np.load(io.BytesIO(raw), allow_pickle=False)
                if array.ndim != 3 or any(d > 256 for d in array.shape) or array.size > 4_194_304:
                    raise ValueError("NPY requires bounded 3D volume")
                if array.dtype.kind not in "buif" or not np.isfinite(array).all():
                    raise ValueError("Volume must contain finite numeric values")
            blobs[artifact.key] = (raw, array.shape, artifact.format)
        except Exception:
            raise HTTPException(422, "Invalid or oversized artifact; use PNG or bounded numeric NPY volumes")
    # Validate spatial compatibility before writing anything.
    for sample in data.samples:
        shapes = {blobs[key][1][:2] if blobs[key][2] == "png" else blobs[key][1] for key in sample.artifacts.values()}
        if len(shapes) > 1:
            raise HTTPException(422, "Sample layers have mismatched geometry")
        if data.dimension == "3D" and any(blobs[key][2] != "npy" for key in sample.artifacts.values()):
            raise HTTPException(422, "3D sample layers require NPY volumes")
        if data.dimension == "2D" and any(blobs[key][2] != "png" for key in sample.artifacts.values()):
            raise HTTPException(422, "2D sample layers require PNG")
    run_id = str(uuid4())
    root = Path(os.getenv("STORAGE_DIR", BASE_DIR / "storage")) / "evaluation" / run_id
    root.mkdir(parents=True, exist_ok=False)
    stored["artifact_metadata"] = {}
    for key, (raw, shape, fmt) in blobs.items():
        (root / f"{key}.{fmt}").write_bytes(raw)
        stored["artifact_metadata"][key] = {"format": fmt, "shape": list(shape)}
    row = EvaluationExperiment(id=run_id, owner_id=user.id, payload_json=json.dumps(stored))
    db.add(row); audit(db, user, "evaluation_imported"); db.commit()
    return output(row, db)


@router.get("/{run_id}/report")
def report(run_id: str, user: User = Depends(readers), db: Session = Depends(get_db)):
    return Response(json.dumps(output(get_run(db, run_id), db), indent=2), media_type="application/json",
                    headers={"Content-Disposition": 'attachment; filename="evaluation-report.json"'})


@router.get("/{run_id}/artifacts/{key}")
def artifact(run_id: str, key: str, slice_index: int = 0, user: User = Depends(readers), db: Session = Depends(get_db)):
    row = get_run(db, run_id)
    meta = json.loads(row.payload_json).get("artifact_metadata", {}).get(key)
    if not meta:
        raise HTTPException(404, "Artifact not found")
    path = Path(os.getenv("STORAGE_DIR", BASE_DIR / "storage")) / "evaluation" / row.id / f'{key}.{meta["format"]}'
    if not path.is_file():
        raise HTTPException(404, "Stored artifact unavailable")
    if meta["format"] == "png":
        return Response(path.read_bytes(), media_type="image/png", headers={"Cache-Control": "no-store"})
    volume = np.load(path, allow_pickle=False, mmap_mode="r")
    if not 0 <= slice_index < volume.shape[0]:
        raise HTTPException(422, "Slice outside stored volume")
    plane = volume[slice_index].astype(float)
    lo, hi = float(volume.min()), float(volume.max())
    plane = (plane - lo) / (hi - lo) if hi > lo else np.full_like(plane, 1 if lo > 0 else 0)
    stream = io.BytesIO(); Image.fromarray((plane * 255).astype("uint8")).save(stream, format="PNG")
    return Response(stream.getvalue(), media_type="image/png", headers={"Cache-Control": "no-store"})


class Review(StrictModel):
    decision: Literal["validation_pending", "approved", "rejected", "retired"]
    notes: str = Field(min_length=10, max_length=4000)
    visual_review_completed: bool = False
    dataset_audit_completed: bool = False


class SampleReview(StrictModel):
    notes: str = Field(min_length=10, max_length=4000)


@router.post("/{run_id}/samples/{sample_id}/review")
def sample_review(run_id: str, sample_id: str, data: SampleReview, user: User = Depends(writers), db: Session = Depends(get_db)):
    row = get_run(db, run_id)
    run = json.loads(row.payload_json)
    if not any(s["id"] == sample_id for s in run["samples"]):
        raise HTTPException(404, "Sample not found")
    db.add(EvaluationSampleReview(experiment_id=row.id, sample_id=sample_id, reviewer_id=user.id, notes=data.notes))
    audit(db, user, "evaluation_sample_reviewed"); db.commit()
    return output(row, db)


@router.post("/{run_id}/review")
def review(run_id: str, data: Review, user: User = Depends(writers), db: Session = Depends(get_db)):
    row = get_run(db, run_id)
    if data.decision == "validation_pending":
        if row.status != "experimental" or user.id != row.owner_id:
            raise HTTPException(409, "Only importer may submit an experimental candidate")
    else:
        if user.role != "admin":
            raise HTTPException(403, "Administrator review required")
        if row.owner_id == user.id:
            raise HTTPException(403, "Independent reviewer required; cannot review own import")
        if data.decision in {"approved", "rejected"} and row.status != "validation_pending":
            raise HTTPException(409, "Candidate must be submitted before decision")
        if data.decision == "retired" and row.status != "approved":
            raise HTTPException(409, "Only approved candidates can be retired")
    if data.decision == "approved":
        run = json.loads(row.payload_json)
        if run.get("execution_status") != "completed":
            raise HTTPException(409, "Failed experiments cannot be approved")
        policy_row = db.get(EvaluationPolicy, run.get("policy_id")) if run.get("policy_id") else None
        if not policy_row or not data.visual_review_completed or not data.dataset_audit_completed:
            raise HTTPException(409, "Predeclared policy, visual review and dataset audit are required")
        policy = json.loads(policy_row.payload_json)
        if policy["task"] != run["task"] or policy["dataset"] != run["dataset"]:
            raise HTTPException(409, "Acceptance policy task, dataset and protocol must match exactly")
        values = {m["name"]: m["value"] for m in run["metrics"]}
        for threshold in policy["thresholds"]:
            value = values.get(threshold["metric"])
            if value is None or (threshold["minimum"] is not None and value < threshold["minimum"]) or (threshold["maximum"] is not None and value > threshold["maximum"]):
                raise HTTPException(409, "Required acceptance threshold not met")
        reviewed = {s.sample_id for s in db.scalars(select(EvaluationSampleReview).where(EvaluationSampleReview.experiment_id == row.id, EvaluationSampleReview.reviewer_id == user.id))}
        if not run["samples"] or not all(s["id"] in reviewed and s["reference_available"] and {"original", "reference", "prediction"} <= set(s["artifacts"]) for s in run["samples"]):
            raise HTTPException(409, "Reference-bound reviewed prediction samples are required")
    # Approval is governance only. This route never writes model registry or weights.
    previous = row.status
    changed = db.execute(update(EvaluationExperiment).where(EvaluationExperiment.id == row.id, EvaluationExperiment.status == previous).values(status=data.decision))
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Candidate status changed; reload before reviewing")
    db.add(EvaluationDecision(experiment_id=row.id, reviewer_id=user.id, decision=data.decision, notes=data.model_dump_json()))
    audit(db, user, f"evaluation_{data.decision}"); db.commit()
    return output(row, db)
