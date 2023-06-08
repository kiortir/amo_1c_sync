from redis.asyncio import Redis

from settings import redis_settings


redis_client: Redis = Redis(
    host=redis_settings.redis_host, port=redis_settings.redis_port
)
