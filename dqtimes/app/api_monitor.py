# app/api_monitor.py
from fastapi import APIRouter
import httpx
import redis
from app.config import get_settings

router = APIRouter(prefix="/monitor", tags=["Monitoramento"])

# URL da sua instância do Flower (definida no docker-compose.yml)
FLOWER_API = "http://flower:5555/api"

@router.get("/status")
async def get_system_status():
    """Retorna métricas do Flower (Celery) e status do Redis"""
    async with httpx.AsyncClient() as client:
        workers_data, tasks_data = {}, {}

        try:
            workers_resp = await client.get(f"{FLOWER_API}/workers")
            tasks_resp = await client.get(f"{FLOWER_API}/tasks?limit=50")

            if workers_resp.status_code == 200:
                workers_data = workers_resp.json()
            if tasks_resp.status_code == 200:
                tasks_data = tasks_resp.json()
        except Exception as e:
            print("⚠️ Erro ao consultar Flower:", e)

        # Resultados Redis
        settings = get_settings()
        redis_status = "disconnected"
        try:
            r = redis.from_url(settings.REDIS_URL)
            r.ping()
            redis_status = "connected"
        except Exception as e:
            print("⚠️ Erro ao conectar ao Redis:", e)

        # Contagem das tarefas
        task_states = {"SUCCESS": 0, "FAILURE": 0, "PENDING": 0}
        try:
            for t in tasks_data.values():
                state = t.get("state", "PENDING")
                if state in task_states:
                    task_states[state] += 1
        except Exception:
            pass

        return {
            "redis": redis_status,
            "workers_total": len(workers_data),
            "task_states": task_states,
            "workers": list(workers_data.keys()),
        }