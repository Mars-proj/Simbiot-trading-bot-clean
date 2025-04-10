import asyncio
import logging
from user_manager import UserManager
from exchange_detector import ExchangeDetector
from ml_predictor import Predictor
from retraining_manager import RetrainingManager
from queue_manager import QueueManager
from notification_manager import NotificationManager
from signal_blacklist import SignalBlacklist
from strategy_manager import StrategyManager

logger = logging.getLogger(__name__)

async def start_trading_all(users, credentials, since, limit, timeframe, symbol_batch, exchange_pool):
    """
    Start trading for all users across multiple exchanges.

    Args:
        users: List of user IDs.
        credentials: Dict of user credentials (API keys).
        since: Timestamp to fetch OHLCV data from (in milliseconds).
        limit: Number of OHLCV candles to fetch.
        timeframe: Timeframe for OHLCV data (e.g., '1h').
        symbol_batch: List of symbols to process.
        exchange_pool: ExchangePool instance for managing exchange connections.
    """
    detector = ExchangeDetector()
    predictor = Predictor()
    retraining_manager = RetrainingManager()
    queue_manager = QueueManager()
    notification_manager = NotificationManager()
    signal_blacklist = SignalBlacklist()
    strategy_manager = StrategyManager()

    for user in users:
        logger.info(f"Starting trading for user {user}")
        await queue_manager.process_user(
            user, credentials[user], since, limit, timeframe, symbol_batch, exchange_pool, detector
        )
        logger.info(f"Finished trading for user {user}")
