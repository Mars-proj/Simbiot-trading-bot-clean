import asyncio
import logging
from celery import Celery

logger = logging.getLogger(__name__)

app = Celery('trading_bot', broker='amqp://guest:guest@localhost/', backend='rpc://')

class QueueManager:
    def __init__(self):
        self.app = app

    async def process_user(self, user, credentials, since, limit, timeframe, symbol_batch):
        logger.info(f"Queuing task for user {user}")
        self.app.send_task(
            'celery_app.process_user_task',
            args=(user, credentials, since, limit, timeframe, symbol_batch),
            queue='celery'
        )
