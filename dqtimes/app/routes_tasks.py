from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from celery.result import AsyncResult
from app.celery_config import celery_app
from app.tasks import dummy_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


class DummyTaskRequest(BaseModel):
    duration: int = 5


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict = None
    error: str = None


@router.post("/dummy", response_model=TaskResponse)
async def create_dummy_task(request: DummyTaskRequest):
    task = dummy_task.apply_async(args=[request.duration])
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message=f"Task enfileirada com ID {task.id}"
    )


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    
    if task_result.state == "PENDING":
        return TaskStatusResponse(
            task_id=task_id,
            status="pending",
            result=None
        )
    elif task_result.state == "STARTED":
        return TaskStatusResponse(
            task_id=task_id,
            status="em_execucao",
            result=None
        )
    elif task_result.state == "SUCCESS":
        return TaskStatusResponse(
            task_id=task_id,
            status="concluida",
            result=task_result.result
        )
    elif task_result.state == "FAILURE":
        return TaskStatusResponse(
            task_id=task_id,
            status="falhou",
            error=str(task_result.info)
        )
    else:
        return TaskStatusResponse(
            task_id=task_id,
            status=task_result.state.lower(),
            result=None
        )
