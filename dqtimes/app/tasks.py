import json
import tempfile
import math
import time
import dask.dataframe as dd
from celery import Task
from app.celery_config import celery_app
from app.aplicacao import forecast_temp


class CallbackTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        pass


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="app.tasks.dummy_task",
    queue="default"
)
def dummy_task(self, duration: int = 5):
    time.sleep(duration)
    return {
        "task_id": self.request.id,
        "status": "completed",
        "message": f"Task dummy executada com sucesso apos {duration} segundos",
        "duration": duration
    }


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="app.tasks.forecast_task",
    queue="forecasts"
)
def forecast_task(self, lista_historico: str, quantidade_projecoes: int):
    lista_original = json.loads(lista_historico)
    n = quantidade_projecoes
    resultado = forecast_temp(lista_original, n)
    return {
        "task_id": self.request.id,
        "projecoes": resultado
    }


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="app.tasks.forecast_dataframe_task",
    queue="forecasts"
)
def forecast_dataframe_task(
    self,
    csv_content: bytes,
    quantidade_projecoes: int,
    header: bool,
    index_col: bool,
    page: int = 1,
    page_size: int = 10
):
    n = quantidade_projecoes

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
        tmp_file.write(csv_content)
        tmp_file_path = tmp_file.name

    ddf = dd.read_csv(tmp_file_path, header=0 if header else None)

    if index_col:
        ddf = ddf.drop(ddf.columns[0], axis=1)

    total_rows = len(ddf)
    total_pages = math.ceil(total_rows / page_size)

    if page > total_pages:
        return {
            "task_id": self.request.id,
            "error": "Page number out of range"
        }

    start_index = (page - 1) * page_size
    end_index = start_index + page_size

    ddf_paginated = ddf.loc[start_index:end_index]

    lista_df = []
    for part in ddf_paginated.to_delayed():
        for index, row in part.compute().iterrows():
            lista_df.append(row.tolist())

    resultado = []
    for lista in lista_df:
        projection = forecast_temp(lista, n)
        resultado.append(projection)

    return {
        "task_id": self.request.id,
        "total_pages": total_pages,
        "current_page": page,
        "projecoes": resultado
    }
