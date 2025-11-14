import redis
from app.config import get_settings

def get_redis_client() -> redis.Redis:
    """Retorna cliente Redis configurado"""
    settings = get_settings()
    return redis.from_url(settings.REDIS_URL, decode_responses=True)

def validate_redis_connection() -> bool:
    """Valida conexão com Redis"""
    try:
        client = get_redis_client()
        client.ping()
        print("✅ Redis conectado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao conectar com Redis: {e}")
        return False