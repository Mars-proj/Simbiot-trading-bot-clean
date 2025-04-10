import asyncio
import logging
from user_manager import UserManager
from exchange_detector import ExchangeDetector
from ml_predictor import Predictor
from retraining_manager import RetrainingManager
from queue_manager import QueueManager
from notification_manager import NotificationManager
from monitoring import Monitoring
from risk_manager import RiskManager
from signal_blacklist import SignalBlacklist
from market_state_analyzer import MarketStateAnalyzer
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
    monitoring = Monitoring()
    risk_manager = RiskManager()
    signal_blacklist = SignalBlacklist()
    market_state_analyzer = MarketStateAnalyzer()
    strategy_manager = StrategyManager()

    for user in users:
        logger.info(f"Starting trading for user {user}")
        await queue_manager.process_user(
            user, credentials[user], since, limit, timeframe, symbol_batch, exchange_pool, detector
        )
        logger.info(f"Finished trading for user {user}")
