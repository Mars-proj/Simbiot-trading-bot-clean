from logging_setup import logger_main
from ohlcv_fetcher import fetch_ohlcv

async def analyze_market_conditions(exchange_id, user_id, timeframe='1h', limit=100, testnet=False, exchange=None):
    """Analyzes market conditions to adjust filtering thresholds."""
    try:
        # Получить данные по основным символам (например, BTCUSDT)
        ohlcv_data = await fetch_ohlcv(exchange_id, "BTCUSDT", user_id, timeframe, limit, testnet, exchange)
        if ohlcv_data is None or ohlcv_data.empty:
            logger_main.warning(f"Failed to fetch market data for BTCUSDT on {exchange_id}")
            return None

        # Рассчитать общую волатильность рынка
        market_volatility = ohlcv_data['close'].pct_change().std() * 100
        # Рассчитать средний объём торгов
        market_volume = ohlcv_data['volume'].mean()

        result = {
            'market_volatility': market_volatility,
            'market_volume': market_volume
        }
        logger_main.info(f"Market conditions for {exchange_id}: volatility={market_volatility}%, volume={market_volume}")
        return result
    except Exception as e:
        logger_main.error(f"Error analyzing market conditions for {exchange_id}: {e}")
        return None

__all__ = ['analyze_market_conditions']
