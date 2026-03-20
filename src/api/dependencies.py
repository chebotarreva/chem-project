from redis import Redis
import os

def get_redis():
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    redis_client = Redis.from_url(redis_url, decode_responses=True)
    try:
        redis_client.ping()
        return redis_client
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Redis unavailable"
        )