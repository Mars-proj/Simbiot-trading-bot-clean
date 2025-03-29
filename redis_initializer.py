import redis.asyncio as redis
from logging_setup import logger_main, logger_exceptions

# Создаём объект redis_client
try:
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        decode_responses=True
    )
    logger_main.info("Redis client initialized successfully")
except Exception as e:
    logger_main.error(f"Failed to initialize Redis client: {str(e)}")
    logger_exceptions.error(f"Redis initialization error: {str(e)}", exc_info=True)
    redis_client = None

__all__ = ['redis_client']
