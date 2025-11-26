import os
import time
from celery import Celery
from datetime import datetime
from datetime import timezone
from celery.signals import task_prerun, task_success, task_failure
from dotenv import load_dotenv
load_dotenv()
from db import SessionLocal, Job

#package de previsao - task #63
from previsao import run_prediction_model

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
    Worker para previsoes
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
        raise ValueError("O parametro 'series' e obrigatorio e deve ser uma LIST")
       
    
    if not periods or not isinstance(periods, int):
        raise ValueError("O parametro 'periods' e obrigatorio e deve ser um INT")
    
    print(f"[{self.request.id}] Delegando previsão para o modulo previsao.py---")
    
    time.sleep(2)
    result_series = run_prediction_model(series, periods)
    
    #retorno formatado
    return {
        "name_ref": name_ref,
        "input_series_len": len(series),
        "prediction": result_series,
        "processed_at": datetime.now(timezone.utc).isoformat()
    }
    

@task_prerun.connect
def on_task_start(sender=None, task_id=None, **kwargs):
    print(f"-- Iniciando Task ID: {task_id}")
    try:
        with SessionLocal() as session:
            job = session.query(Job).filter_by(task_id=task_id).first()
            if job:
                job.status = "IN_PROGRESS"
                job.started_at = datetime.now(timezone.utc)
                session.commit()
    except Exception as e:
        print(f"Erro ao atualziar status IN_PROGRESS: {e}")


@task_success.connect
def on_task_success(sender=None, result=None, task_id=None, **kwargs):
    if not task_id and sender and hasattr(sender, 'request'):
        task_id = sender.request.id
        
    print(f"-- Sucesso Task ID: {task_id}")
    
    try:
        with SessionLocal() as session:
            job = session.query(Job).filter_by(task_id=task_id).first()
            if job:
                job.status = "SUCCESS"
                job.finished_at = datetime.now(timezone.utc)
                job.result = result
                session.commit()
            else: 
                print(f"ALERT: Job {task_id} não encontrado no banco para atualizar")
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
                job.finished_at = datetime.now(timezone.utc)
                job.result = {"error": str(exception)}
                session.commit()
    except Exception as e:
        print(f"Erro ao atualizar status FAILURE: {e}")
        
