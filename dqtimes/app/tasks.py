import os
import time
from celery import Celery
from datetime import datetime
from celery.signals import task_prerun, task_success, task_failure
from dotenv import load_dotenv
load_dotenv()
from db import SessionLocal, Job

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")

celery_app = Celery("tasks", broker=CELERY_BROKER_URL)

#Config pra impedir que o Worker trave com tarefas extensas

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=300 #tempo em segundos(5minutos)
)


@celery_app.task(name="predict", bind=True)
def predict(self, payload):
    """
    Worker para previsões
    Espera um payload: {
        "series": [10, 20, 30...],
        "name_ref": "nome-modelo || uid"
        "periods": 3
    }
    """
    series = payload.get("series")
    name_ref = payload.get('name_ref')
    periods = payload.get('periods')
    
    if not series or not isinstance(series, list):
        raise ValueError("O parametro 'series' e obrigatorio e deve ser um Array")
    
    if not periods or not isinstance(periods, int):
        raise ValueError("O parametro 'periods' e obrigatorio e deve ser um Int")
    
    print(f"[{self.request.id}] Iniciando previsão para '{name_ref}' com {periods} periodos -")
    
    #Simula processamento para testar o worker consumindo a fila
    time.sleep(5)
    
    #Mock resultado
    prediction_mock = [x * 1.05 for x in series[-periods:]]
    
    return {
        "name_ref": name_ref,
        "input_series_len": len(series),
        "prediction": prediction_mock,
        "processed_at": datetime.utcnow().isoformat()
    }

@task_prerun.connect
def on_task_start(sender=None, task_id=None, **kwargs):
    print(f"-- Iniciando Task ID: {task_id}")
    try:
        with SessionLocal() as session:
            job = session.query(Job).filter_by(task_id=task_id).first()
            if job:
                job.status = "IN_PROGRESS"
                job.started_at = datetime.utcnow()
                session.commit()
    except Exception as e:
        print(f"Erro ao atualziar status IN_PROGRESS: {e}")

@task_success.connect
def on_task_success(sender=None, result=None, task_id=None, **kwargs):
    print(f"-- Sucesso Task ID: {task_id}")
    try:
        with SessionLocal() as session:
            job = session.query(Job).filter_by(task_id=task_id).first()
            if job:
                job.status = "SUCCESS"
                job.finished_at = datetime.utcnow()
                job.result = result
                session.commit()
    except Exception as e:
        print(f"Erro ao atualizar status SUCCESS: {e}")

@task_failure.connect
def on_task_failure(sender=None, task_id=None, exception=None, **kwargs):
    print(f"-- Falha Task ID: {task_id}")
    try:
        with SessionLocal() as session:
            job = session.query(Job).filter_by(task_id=task_id).first()
            if job:
                job.status = "FAILURE"
                job.finished_at = datetime.utcnow()
                job.result = {"error": str(exception)}
                session.commit()
    except Exception as e:
        print(f"Erro ao atualizar status FAILURE: {e}")
        
