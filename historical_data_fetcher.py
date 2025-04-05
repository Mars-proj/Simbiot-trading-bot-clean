import asyncio
import time
import json
import os
from logging_setup import logger_main
from pycoingecko import CoinGeckoAPI
from datetime import datetime

# Path to cache file for CoinGecko coins list
COINGECKO_CACHE_FILE = "coingecko_coins.json"
COINGECKO_CACHE_DURATION = 24 * 60 * 60  # 24 hours in seconds
COINGECKO_MAX_DAYS = 365  # Maximum days allowed for free CoinGecko plan
COINGECKO_OPTIMAL_DAYS = 90  # Optimal range for hourly data (up to 90 days)

async def fetch_historical_data(exchange_id, user_id, symbol, since, testnet=False, exchange=None, limit=2000):
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
            # Adjust 'since' to not exceed CoinGecko's 365-day limit
            max_since = int(time.time()) - COINGECKO_MAX_DAYS * 24 * 60 * 60
            adjusted_since = max(since, max_since)
            if adjusted_since > since:
                logger_main.warning(f"Adjusted 'since' from {since} to {adjusted_since} to fit CoinGecko's 365-day limit")
            ohlcv = await fetch_from_coingecko(symbol, adjusted_since, limit)
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
    """Fetches historical OHLCV data from CoinGecko using market chart data."""
    try:
        cg = CoinGeckoAPI()
        # Convert symbol to CoinGecko ID
        coin_id = await symbol_to_coingecko_id(symbol)
        if not coin_id:
            logger_main.warning(f"Could not map {symbol} to CoinGecko ID")
            return None

        # Ensure 'since' is not older than CoinGecko's limit
        max_since = int(time.time()) - COINGECKO_MAX_DAYS * 24 * 60 * 60
        adjusted_since = max(since // 1000, max_since)  # Convert milliseconds to seconds
        to_timestamp = int(time.time())

        # Optimize range to get hourly data (up to 90 days)
        optimal_since = int(time.time()) - COINGECKO_OPTIMAL_DAYS * 24 * 60 * 60
        adjusted_since = max(adjusted_since, optimal_since)
        if to_timestamp - adjusted_since < 3600:  # Ensure at least 1 hour range
            adjusted_since = to_timestamp - 3600

        logger_main.debug(f"Fetching CoinGecko data for {symbol} from {adjusted_since} to {to_timestamp}")

        # Fetch historical market data from CoinGecko (hourly data for ranges < 90 days)
        data = cg.get_coin_market_chart_range_by_id(
            id=coin_id,
            vs_currency='usd',
            from_timestamp=adjusted_since,
            to_timestamp=to_timestamp
        )
        if not data or 'prices' not in data or not data['prices']:
            logger_main.warning(f"No historical data available for {symbol} on CoinGecko")
            return None

        # Convert market chart data to OHLCV format
        ohlcv = []
        prices = data['prices']  # List of [timestamp, price]
        for i in range(min(len(prices) - 1, limit)):  # Limit the number of entries
            timestamp = prices[i][0]  # Unix timestamp in milliseconds
            open_price = prices[i][1]
            close_price = prices[i + 1][1]
            high_price = max(open_price, close_price)
            low_price = min(open_price, close_price)
            volume = data['total_volumes'][i][1] if 'total_volumes' in data else 0
            ohlcv.append([timestamp, open_price, high_price, low_price, close_price, volume])

        return ohlcv

    except Exception as e:
        logger_main.error(f"Error fetching historical data from CoinGecko for {symbol}: {e}")
        return None

async def symbol_to_coingecko_id(symbol):
    """Maps a symbol to a CoinGecko ID using a cached coins list."""
    try:
        cg = CoinGeckoAPI()
        # Load or fetch the CoinGecko coins list
        coins_list = await get_coingecko_coins_list(cg)

        # Remove USDT/USDC suffix and convert to lowercase
        base_symbol = symbol.replace("USDT", "").replace("USDC", "").lower()

        # Search for the symbol in the coins list
        for coin in coins_list:
            if coin['symbol'].lower() == base_symbol:
                logger_main.debug(f"Mapped {symbol} to CoinGecko ID: {coin['id']}")
                return coin['id']

        logger_main.warning(f"No CoinGecko ID found for {symbol}")
        return None

    except Exception as e:
        logger_main.error(f"Error mapping symbol {symbol} to CoinGecko ID: {e}")
        return None

async def get_coingecko_coins_list(cg):
    """Fetches or loads the cached CoinGecko coins list."""
    try:
        # Check if cache file exists and is fresh
        if os.path.exists(COINGECKO_CACHE_FILE):
            with open(COINGECKO_CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
            cache_time = cache_data.get('timestamp', 0)
            if time.time() - cache_time < COINGECKO_CACHE_DURATION:
                logger_main.debug("Using cached CoinGecko coins list")
                return cache_data['coins']

        # Fetch the coins list from CoinGecko
        logger_main.info("Fetching CoinGecko coins list")
        coins_list = cg.get_coins_list()
        if not coins_list:
            logger_main.error("Failed to fetch CoinGecko coins list")
            return []

        # Cache the coins list
        cache_data = {
            'timestamp': int(time.time()),
            'coins': coins_list
        }
        with open(COINGECKO_CACHE_FILE, 'w') as f:
            json.dump(cache_data, f)
        logger_main.info(f"Cached {len(coins_list)} coins from CoinGecko")

        return coins_list

    except Exception as e:
        logger_main.error(f"Error fetching CoinGecko coins list: {e}")
        return []
