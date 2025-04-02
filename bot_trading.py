from logging_setup import logger_main
from bot_user_data import user_data
from ohlcv_fetcher import fetch_ohlcv
from signal_generator_dynamic import generate_dynamic_signals
from cache_utils import CacheUtils
import time

async def run_trading_bot(exchange_id, user_id, symbol, leverage=1.0, order_type='limit', trade_percentage=0.1, rsi_overbought=70, rsi_oversold=30, margin_multiplier=2.0, model_path=None, test_mode=False):
    """Runs the trading bot for a single symbol."""
    try:
        logger_main.info(f"Starting trading bot for {symbol} on {exchange_id} for user {user_id}")
        
        # Fetch real-time data
        ohlcv_data = await fetch_ohlcv(exchange_id, symbol, user_id, timeframe='1h', limit=100, testnet=test_mode)
        if ohlcv_data is None or ohlcv_data.empty:
            logger_main.error(f"Failed to fetch real-time data for {symbol} on {exchange_id}")
            return False

        # Generate signal
        signal = await generate_dynamic_signals(exchange_id, user_id, symbol, timeframe='1h', limit=100, testnet=test_mode)
        if signal is None:
            logger_main.warning(f"No trading signal for {symbol} on {exchange_id}")
            return False

        # Simulate a trade (in test mode) or execute a real trade
        current_price = ohlcv_data['close'].iloc[-1]
        trade_data = {
            'exchange_id': exchange_id,
            'user_id': user_id,
            'symbol': symbol,
            'trade_type': signal,
            'price': current_price,
            'volume': trade_percentage * leverage,  # Placeholder volume
            'timestamp': int(ohlcv_data['timestamp'].iloc[-1]),
            'profit_loss': 0.0  # Placeholder, to be updated later
        }

        # Save trade to pool
        cache = CacheUtils()
        key = f"trade_pool:{exchange_id}:{user_id}"
        await cache.append_to_list(key, trade_data)
        logger_main.info(f"Trade executed for {symbol} on {exchange_id}: {trade_data}")
        return True
    except Exception as e:
        logger_main.error(f"Error running trading bot for {symbol} on {exchange_id} for user {user_id}: {e}")
        return False

__all__ = ['run_trading_bot']
