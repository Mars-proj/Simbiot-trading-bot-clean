from celery import Celery
import logging
import asyncio

logger = logging.getLogger("celery")

app = Celery('trading_bot', broker='amqp://guest:guest@localhost/', backend='rpc://')

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 час на выполнение задачи
    task_soft_time_limit=3000,  # Мягкий лимит 50 минут
    worker_prefetch_multiplier=1,  # Обрабатывать по одной задаче за раз
    task_acks_late=True,  # Подтверждать выполнение после завершения
)

@app.task(bind=True, retry_backoff=True, max_retries=3)
def process_user_task(self, user, credentials, since, limit, timeframe, symbol_batch, exchange_pool, detector):
    """
    Process trading task for a user.

    Args:
        user: User identifier.
        credentials: User's API credentials.
        since: Timestamp to fetch OHLCV data from (in milliseconds).
        limit: Number of OHLCV candles to fetch.
        timeframe: Timeframe for OHLCV data (e.g., '1h').
        symbol_batch: List of symbols to process.
        exchange_pool: ExchangePool instance.
        detector: ExchangeDetector instance.
    """
    logger.info(f"Starting task for user {user} with {len(symbol_batch)} symbols")
    from core import process_user
    try:
        # Вызываем асинхронную функцию через asyncio.run()
        asyncio.run(process_user(user, credentials, since, limit, timeframe, symbol_batch, exchange_pool, detector))
        logger.info(f"Task completed for user {user}")
    except Exception as e:
        logger.error(f"Task failed for user {user}: {type(e).__name__}: {str(e)}")
        self.retry(countdown=60)
