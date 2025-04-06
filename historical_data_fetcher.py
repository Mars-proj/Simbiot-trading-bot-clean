import asyncio
import aiohttp
import json
import os
import time
from logging_setup import logger_main
import pandas as pd

# Cache for CoinGecko coins list
COINGECKO_COINS_CACHE = None
COINGECKO_COINS_CACHE_FILE = "coingecko_coins.json"

# Cache for historical data
HISTORICAL_DATA_CACHE = {}
HISTORICAL_DATA_CACHE_FILE = "historical_data_cache.json"

# Semaphore to limit concurrent requests to CoinGecko
COINGECKO_SEMAPHORE = asyncio.Semaphore(10)  # Limit to 10 concurrent requests

async def fetch_historical_data(exchange_id, user_id, symbol, since, testnet=False, exchange=None, limit=2000):
    """Fetches historical OHLCV data for a given symbol."""
    logger_main.info(f"Fetching historical data for {symbol} on {exchange_id} for user {user_id} with limit {limit}")
    
    # Try to fetch from exchange first
    if exchange:
        try:
            logger_main.debug(f"Attempting to fetch data for {symbol} from exchange with since={since}")
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe='1h', since=since * 1000, limit=limit)
            if ohlcv:
                logger_main.info(f"Fetched {len(ohlcv)} OHLCV data points for {symbol} from exchange")
                return ohlcv
            else:
                logger_main.info(f"No data available for {symbol} on {exchange_id}, trying CoinGecko")
        except Exception as e:
            logger_main.warning(f"Failed to fetch data for {symbol} from exchange: {e}, trying CoinGecko")

    # Fallback to CoinGecko
    async with COINGECKO_SEMAPHORE:  # Limit concurrent requests
        return await fetch_from_coingecko(symbol, since, limit)

async def fetch_from_coingecko(symbol, since, limit):
    """Fetches historical OHLCV data from CoinGecko."""
    # Load CoinGecko coins list if not already loaded
    global COINGECKO_COINS_CACHE
    if COINGECKO_COINS_CACHE is None:
        if os.path.exists(COINGECKO_COINS_CACHE_FILE):
            with open(COINGECKO_COINS_CACHE_FILE, 'r') as f:
                COINGECKO_COINS_CACHE = json.load(f)
            logger_main.debug("Using cached CoinGecko coins list")
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.coingecko.com/api/v3/coins/list') as response:
                    COINGECKO_COINS_CACHE = await response.json()
                    with open(COINGECKO_COINS_CACHE_FILE, 'w') as f:
                        json.dump(COINGECKO_COINS_CACHE, f)
                    logger_main.debug("Fetched and cached CoinGecko coins list")

    # Map symbol to CoinGecko ID
    base = symbol.split('USDT')[0]
    coin = next((c for c in COINGECKO_COINS_CACHE if c['symbol'].lower() == base.lower()), None)
    if not coin:
        logger_main.warning(f"No CoinGecko ID found for {symbol}")
        logger_main.warning(f"Could not map {symbol} to CoinGecko ID, adding to problematic symbols")
        return None
    coingecko_id = coin['id']
    logger_main.debug(f"Mapped {symbol} to CoinGecko ID: {coingecko_id}")

    # Check cache
    cache_key = f"{symbol}:{since}:{limit}"
    if cache_key in HISTORICAL_DATA_CACHE:
        logger_main.debug(f"Using cached historical data for {cache_key}")
        return HISTORICAL_DATA_CACHE[cache_key]

    # Fetch historical data from CoinGecko
    since_timestamp = since
    current_timestamp = int(time.time())
    logger_main.debug(f"Fetching CoinGecko data for {symbol} from {since_timestamp} to {current_timestamp}")

    url = f"https://api.coingecko.com/api/v3/coins/{coingecko_id}/market_chart/range"
    params = {
        'vs_currency': 'usd',
        'from': since_timestamp,
        'to': current_timestamp
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status != 200:
                logger_main.warning(f"Failed to fetch historical data for {symbol} from CoinGecko: {response.status}")
                return None
            try:
                data = await response.json()
                if not isinstance(data, dict):
                    logger_main.warning(f"Unexpected response format for {symbol} from CoinGecko: {data}")
                    return None
                prices = data.get('prices', [])
                if not prices:
                    logger_main.warning(f"No historical data available for {symbol} on CoinGecko")
                    return None

                # Convert to OHLCV format
                ohlcv = []
                for price in prices[:limit]:
                    if not isinstance(price, list) or len(price) < 2:
                        logger_main.warning(f"Invalid price data for {symbol}: {price}")
                        continue
                    timestamp = price[0] // 1000  # Convert milliseconds to seconds
                    ohlcv.append([timestamp, price[1], price[1], price[1], price[1], 0])
                logger_main.info(f"Fetched {len(ohlcv)} OHLCV data points for {symbol} from CoinGecko")

                # Cache the result
                HISTORICAL_DATA_CACHE[cache_key] = ohlcv
                with open(HISTORICAL_DATA_CACHE_FILE, 'w') as f:
                    json.dump(HISTORICAL_DATA_CACHE, f)
                logger_main.debug(f"Cached historical data for {cache_key}")

                return ohlcv
            except Exception as e:
                logger_main.warning(f"Error processing CoinGecko response for {symbol}: {e}")
                return None
