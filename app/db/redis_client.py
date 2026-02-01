import redis.asyncio as redis
from app.core.config import settings

async def get_redis():
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return r

# Usage:
# redis_client = await get_redis()
