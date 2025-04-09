ncio as redis
import logging

logger = logging.getLogger("main")

async def get_redis_client():
    return await redis.from_url("redis://localhost:6379/0")

class SignalBlacklist:
    """
    Manage a blacklist of signals with Redis storage.
    """

    def __init__(self):
        self.redis_key = "signal_blacklist"

    async def add_to_blacklist(self, signal):
        """
        Add a signal to the blacklist in Redis.

        Args:
            signal (str): Signal to blacklist.
        """
        redis_client = await get_redis_client()
        try:
            await redis_client.sadd(self.redis_key, signal)
            logger.debug(f"Added signal {signal} to blacklist")
        except Exception as e:
            logger.error(f"Failed to add signal {signal} to blacklist: {type(e).__name__}: {str(e)}")
        finally:
            await redis_client.close()

    async def is_blacklisted(self, signal):
        """
        Check if a signal is blacklisted.

        Args:
            signal (str): Signal to check.

        Returns:
            bool: True if blacklisted, False otherwise.
        """
        redis_client = await get_redis_client()
        try:
            return await redis_client.sismember(self.redis_key, signal)
        except Exception as e:
            logger.error(f"Failed to check if signal {signal} is blacklisted: {type(e).__name__}: {str(e)}")
            return False
        finally:
            await redis_client.close()

    async def remove_from_blacklist(self, signal):
        """
        Remove a signal from the blacklist.

        Args:
            signal (str): Signal to remove.
        """
        redis_client = await get_redis_client()
        try:
            await redis_client.srem(self.redis_key, signal)
            logger.debug(f"Removed signal {signal} from blacklist")
        except Exception as e:
            logger.error(f"Failed to remove signal {signal} from blacklist: {type(e).__name__}: {str(e)}")
        finally:
            await redis_client.close()
