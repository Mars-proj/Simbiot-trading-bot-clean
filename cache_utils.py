# cache_utils.py
import redis
from logging_setup import logger_main

class RedisClient:
    def __init__(self, url):
        try:
            self.client = redis.Redis.from_url(url, decode_responses=True)
            logger_main.info(f"Initialized Redis client with URL: {url}")
        except Exception as e:
            logger_main.error(f"Failed to initialize Redis client: {e}")
            raise

    def get_list(self, key):
        try:
            logger_main.debug(f"Retrieving list for key: {key}")
            result = self.client.lrange(key, 0, -1)
            logger_main.debug(f"Retrieved list for key {key}: {result}")
            return result
        except Exception as e:
            logger_main.error(f"Error retrieving list {key}: {e}\n{traceback.format_exc()}")
            raise

    def set_list(self, key, value):
        try:
            logger_main.debug(f"Setting list for key: {key} with value: {value}")
            # Удаляем старую запись, если она существует
            self.client.delete(key)
            # Добавляем элементы в список
            if value:
                self.client.rpush(key, *value)
            logger_main.debug(f"Set list for key {key}")
        except Exception as e:
            logger_main.error(f"Error setting list {key}: {e}\n{traceback.format_exc()}")
            raise
