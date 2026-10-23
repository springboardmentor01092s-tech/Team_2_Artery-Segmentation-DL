"""Persistent single-process inference queue. No training, subprocesses or silent retries.

Deploy exactly one API worker. Interrupted processing jobs fail on restart; pending
jobs remain restartable. For multi-host operation use an external leased worker.
"""
from datetime import timedelta
from threading import Event, Thread

from sqlalchemy import select, update
from .database import SessionLocal
from .models import AnalysisJob, AuditEvent, Case, now


class InferenceWorker:
    def __init__(self, execute):
        self.execute = execute
        self.stop = Event()
        self.thread = Thread(target=self.run, name="corovision-inference", daemon=True)

    def start(self):
        # Only one API process is supported. Do not reclaim jobs in another process.
        with SessionLocal() as db:
            for job in db.scalars(select(AnalysisJob).where(AnalysisJob.status == "processing")):
                self.fail(db, job, "worker_interrupted", "Worker stopped before completion; review and explicitly request a new run.")
            db.commit()
        self.thread.start()

    def close(self):
        self.stop.set()
        self.thread.join(timeout=5)

    @staticmethod
    def fail(db, job, code, detail):
        job.status, job.error_code, job.error_detail = "failed", code, detail
        job.active_image_id = None
        job.completed_at = now()
        case = db.get(Case, job.case_id)
        if case:
            case.processing_status = "failed"
        db.add(AuditEvent(user_id=job.requested_by, case_id=job.case_id, action="analysis_job_failed:" + code))

    def tick(self):
        with SessionLocal() as db:
            job = db.scalar(select(AnalysisJob).where(AnalysisJob.status == "pending").order_by(AnalysisJob.created_at))
            if not job:
                return False
            identity = job.id
            claimed = db.execute(update(AnalysisJob).where(AnalysisJob.id == identity, AnalysisJob.status == "pending")
                                 .values(status="processing", started_at=now(), progress=10))
            db.commit()
            if not claimed.rowcount:
                return True
            db.refresh(job)
            case = db.get(Case, job.case_id)
            if case:
                case.processing_status = 'processing'
                db.commit()
            try:
                # Bound stale queue work; this is not a hard inference time limit.
                if job.created_at.replace(tzinfo=now().tzinfo) < now() - timedelta(minutes=30):
                    self.fail(db, job, "queue_expired", "Queued request expired; explicitly submit a new run.")
                    db.commit()
                else:
                    self.execute(db, job)
            except Exception:
                # Never expose checkpoint paths, decoder internals or medical filenames.
                db.rollback()
                job = db.get(AnalysisJob, identity)
                if job and job.status != "completed":
                    self.fail(db, job, "analysis_unavailable", "Analysis failed; check model availability, case access and input integrity.")
                    db.commit()
            return True

    def run(self):
        while not self.stop.is_set():
            try:
                worked = self.tick()
            except Exception:
                # Temporary database failure leaves persisted state for restart review.
                worked = False
            if not worked:
                self.stop.wait(.5)
