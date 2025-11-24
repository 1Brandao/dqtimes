from celery import Celery
from datetime import datetime
from celery.signals import task_prerun, task_success, task_failure
from db import SessionLocal, Job
import os

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")

celery_app = Celery("tasks", broker=CELERY_BROKER_URL)

@celery_app.task(name="predict")
def predict(payload):
    return {"payload": payload, "processed_at": datetime.utcnow().isoformat()}

@task_prerun.connect
def on_task_start(sender=None, task_id=None, **kwargs):
    with SessionLocal() as session:
        job = session.query(Job).filter_by(task_id=task_id).first()
        if job:
            job.status = "IN_PROGRESS"
            job.started_at = datetime.utcnow()
            session.commit()

@task_success.connect
def on_task_success(sender=None, result=None, task_id=None, **kwargs):
    with SessionLocal() as session:
        job = session.query(Job).filter_by(task_id=task_id).first()
        if job:
            job.status = "SUCCESS"
            job.finished_at = datetime.utcnow()
            job.result = result
            session.commit()

@task_failure.connect
def on_task_failure(sender=None, task_id=None, exception=None, **kwargs):
    with SessionLocal() as session:
        job = session.query(Job).filter_by(task_id=task_id).first()
        if job:
            job.status = "FAILURE"
            job.finished_at = datetime.utcnow()
            job.result = {"error": str(exception)}
            session.commit()
