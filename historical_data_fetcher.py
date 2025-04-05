import asyncio
import time
from logging_setup import logger_main
from pycoingecko import CoinGeckoAPI
from datetime import datetime

async def fetch_historical_data(exchange_id, user_id, symbol, since, testnet=False, exchange=None, limit=1000):
    """Fetches historical OHLCV data for a symbol with configurable limit and iterative time range."""
    logger_main.info(f"Fetching historical data for {symbol} on {exchange_id} for user {user_id} with limit {limit}")
    try:
        if exchange is None:
            from exchange_pool import ExchangePool
            exchange_pool = ExchangePool()
            exchange = await exchange_pool.get_exchange(exchange_id, user_id, testnet)
            if not exchange:
                logger_main.error(f"Failed to get exchange instance for {exchange_id}:{user_id}")
                return None

        # Try fetching data from the exchange first
        time_ranges = [
            since,  # Original since value (e.g., 90 days ago)
            int(time.time()) - 30 * 24 * 60 * 60,  # 30 days ago
            int(time.time()) - 7 * 24 * 60 * 60,   # 7 days ago
            int(time.time()) - 1 * 24 * 60 * 60    # 1 day ago
        ]

        ohlcv = []
        for attempt_since in time_ranges:
            logger_main.debug(f"Attempting to fetch data for {symbol} from exchange with since={attempt_since}")
            try:
                ohlcv = await exchange.fetch_ohlcv(symbol, '1h', since=attempt_since, limit=limit)
                if ohlcv:
                    logger_main.debug(f"Fetched {len(ohlcv)} OHLCV data points for {symbol} with since={attempt_since} from exchange")
                    break
            except Exception as e:
                logger_main.warning(f"Failed to fetch data for {symbol} from exchange with since={attempt_since}: {e}")
                continue

        # If exchange data is not available, try CoinGecko
        if not ohlcv:
            logger_main.info(f"No data available for {symbol} on {exchange_id}, trying CoinGecko")
            ohlcv = await fetch_from_coingecko(symbol, since, limit)
            if ohlcv:
                logger_main.info(f"Fetched {len(ohlcv)} OHLCV data points for {symbol} from CoinGecko")
            else:
                logger_main.warning(f"No historical data available for {symbol} after multiple attempts")
                if exchange_id is None:
                    await exchange_pool.close_exchange(exchange_id, user_id)
                return None

        if exchange_id is None:
            await exchange_pool.close_exchange(exchange_id, user_id)
        return ohlcv

    except Exception as e:
        logger_main.error(f"Error fetching historical data for {symbol}: {e}")
        return None

async def fetch_from_coingecko(symbol, since, limit):
    """Fetches historical OHLCV data from CoinGecko."""
    try:
        cg = CoinGeckoAPI()
        # Convert symbol to CoinGecko ID (e.g., BTCUSDT -> bitcoin)
        coin_id = symbol_to_coingecko_id(symbol)
        if not coin_id:
            logger_main.warning(f"Could not map {symbol} to CoinGecko ID")
            return None

        # CoinGecko API expects days for historical data
        days = (int(time.time()) - since) // (24 * 60 * 60)  # Convert seconds to days
        if days < 1:
            days = 1  # Minimum 1 day

        # Fetch historical OHLCV data from CoinGecko (daily data)
        data = cg.get_coin_ohlc_by_id(id=coin_id, vs_currency='usd', days=days)
        if not data:
            logger_main.warning(f"No historical data available for {symbol} on CoinGecko")
            return None

        # Convert daily data to hourly (approximate)
        ohlcv = []
        for entry in data[:limit]:  # Limit the number of entries
            timestamp = entry[0]  # Unix timestamp in milliseconds
            open_price = entry[1]
            high_price = entry[2]
            low_price = entry[3]
            close_price = entry[4]
            # Approximate volume (CoinGecko OHLC doesn't provide volume, so we set to 0)
            volume = 0
            ohlcv.append([timestamp, open_price, high_price, low_price, close_price, volume])

        return ohlcv

    except Exception as e:
        logger_main.error(f"Error fetching historical data from CoinGecko for {symbol}: {e}")
        return None

def symbol_to_coingecko_id(symbol):
    """Maps a symbol to a CoinGecko ID."""
    # Simple mapping for common symbols (can be expanded)
    symbol = symbol.replace("USDT", "").replace("USDC", "")
    mapping = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "BNB": "binancecoin",
        "XRP": "ripple",
        "ADA": "cardano",
        # Add more mappings as needed
    }
    return mapping.get(symbol.upper(), symbol.lower())
