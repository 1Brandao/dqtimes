from flask import Flask, request, jsonify
from datetime import datetime
from tasks import celery_app
from db import SessionLocal, Job

app = Flask(__name__)

@app.post("/predict")
def create_prediction():
    payload = request.get_json(force=True)
    async_result = celery_app.send_task("predict", args=[payload])

    with SessionLocal() as session:
        job = Job(
            task_id=async_result.id,
            status="PENDING",
            created_at=datetime.utcnow(),
            payload=payload,
        )
        session.add(job)
        session.commit()

    return jsonify({"task_id": async_result.id, "status": "PENDING"}), 202

@app.get("/status/<task_id>")
def status(task_id):
    with SessionLocal() as session:
        job = session.query(Job).filter_by(task_id=task_id).first()
        if not job:
            return jsonify({"error": "not_found"}), 404

        return jsonify({
            "task_id": job.task_id,
            "status": job.status,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
            "payload": job.payload,
            "result": job.result,
        })
