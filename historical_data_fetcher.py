# historical_data_fetcher.py
import logging

logger = logging.getLogger("main")

async def fetch_historical_data(symbol, exchange, since, limit, timeframe, user):
    try:
        logger.debug(f"Fetching OHLCV data for {symbol} with timeframe {timeframe}, since={since}, limit={limit}")
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, since, limit)
        logger.debug(f"Fetched {len(ohlcv)} OHLCV data points for {symbol}")
        return ohlcv
    except Exception as e:
        logger.error(f"Failed to fetch OHLCV data for {symbol}: {type(e).__name__}: {str(e)}")
        raise
