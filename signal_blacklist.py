import redis
import logging

logger = logging.getLogger(__name__)

class SignalBlacklist:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

    def add_signal(self, signal_id):
        """
        Add a signal to the blacklist.

        Args:
            signal_id: ID of the signal to blacklist.
        """
        self.redis.sadd('blacklist:signals', signal_id)
        logger.info(f"Added signal {signal_id} to blacklist")

    def is_blacklisted(self, signal_id):
        """
        Check if a signal is blacklisted.

        Args:
            signal_id: ID of the signal to check.

        Returns:
            bool: True if blacklisted, False otherwise.
        """
        return self.redis.sismember('blacklist:signals', signal_id)
