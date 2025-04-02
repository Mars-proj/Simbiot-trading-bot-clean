import aiohttp
import asyncio
from logging_setup import logger_main
from exchange_factory import create_exchange
from symbol_handler import validate_symbol
from cache_utils import CacheUtils
from token_analyzer import analyze_token
from signal_generator_indicators import calculate_rsi
from signal_generator_dynamic import generate_dynamic_signals
from ohlcv_fetcher import fetch_ohlcv
from market_analyzer import analyze_market_conditions

async def get_test_symbols(exchange_id, user_id, testnet=False):
    """Fetches a list of test symbols dynamically from the exchange with volume filtering."""
    exchange = None
    try:
        logger_main.info(f"Starting to fetch test symbols for {exchange_id} (user: {user_id}, testnet: {testnet})")
        
        # Create a single exchange instance
        exchange = create_exchange(exchange_id, user_id, testnet=testnet)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return []

        logger_main.info(f"Exchange instance created, loading markets for {exchange_id}")
        
        # Check if symbols are already cached
        cache = CacheUtils()
        cache_key = f"symbols:{exchange_id}:{'testnet' if testnet else 'live'}"
        cached_symbols = await cache.get(cache_key)
        if cached_symbols:
            logger_main.info(f"Loaded {len(cached_symbols)} symbols from cache for {exchange_id}")
            symbols = cached_symbols
        else:
            # Load markets with retries and timeout
            max_retries = 3
            retry_delay = 5  # seconds
            symbols = []
            for attempt in range(max_retries):
                try:
                    await asyncio.wait_for(exchange.load_markets(), timeout=30)  # 30 seconds timeout
                    logger_main.info(f"Markets loaded for {exchange_id}, total symbols: {len(exchange.markets)}")
                    symbols = list(exchange.markets.keys())
                    break
                except asyncio.TimeoutError:
                    logger_main.error(f"Timeout while loading markets for {exchange_id} (attempt {attempt + 1}/{max_retries})")
                    if attempt + 1 == max_retries:
                        logger_main.error(f"Failed to load markets after {max_retries} attempts")

            # If load_markets failed, fetch symbols via public API
            if not symbols:
                logger_main.warning(f"load_markets() failed, fetching symbols via public API for {exchange_id}")
                async with aiohttp.ClientSession() as session:
                    if exchange_id == "mexc":
                        url = "https://api.mexc.com/api/v3/exchangeInfo"
                    else:
                        logger_main.error(f"No public API fetch implemented for {exchange_id}")
                        return []

                    try:
                        async with session.get(url) as response:
                            if response.status != 200:
                                logger_main.error(f"Failed to fetch exchange info from {exchange_id}: HTTP {response.status}")
                                # Fallback to hardcoded list if API fails
                                symbols = ["BTCUSDT", "ETHUSDT", "XRPUSDT"]
                                logger_main.warning(f"Using hardcoded symbols list: {symbols}")
                            else:
                                data = await response.json()
                                # Check for MEXC status "1" and spot trading allowed
                                symbols = [
                                    market['symbol']
                                    for market in data.get('symbols', [])
                                    if market.get('status') == "1" and market.get('isSpotTradingAllowed', False)
                                ]
                                logger_main.info(f"Fetched {len(symbols)} symbols via public API for {exchange_id}: {symbols[:5]}...")
                    except Exception as e:
                        logger_main.error(f"Error fetching symbols via public API for {exchange_id}: {e}")
                        # Fallback to hardcoded list if API fails
                        symbols = ["BTCUSDT", "ETHUSDT", "XRPUSDT"]
                        logger_main.warning(f"Using hardcoded symbols list: {symbols}")

            if not symbols:
                logger_main.error(f"No symbols available for {exchange_id}, stopping")
                return []

            # Cache the symbols
            await cache.setex(cache_key, 86400, symbols)  # Cache for 24 hours
            logger_main.info(f"Cached {len(symbols)} symbols for {exchange_id}")

        # Pre-filter symbols by volume
        async with aiohttp.ClientSession() as session:
            url = f"https://api.mexc.com/api/v3/ticker/24hr"
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger_main.warning(f"Failed to fetch ticker data for pre-filtering: HTTP {response.status}")
                    else:
                        data = await response.json()
                        volume_data = {item['symbol']: float(item['volume']) for item in data}
                        symbols = [
                            symbol for symbol in symbols
                            if volume_data.get(symbol, 0) >= 10  # Сниженный порог для предварительной фильтрации
                        ]
                        logger_main.info(f"Pre-filtered {len(symbols)} symbols by volume: {symbols[:5]}...")
            except Exception as e:
                logger_main.error(f"Error pre-filtering symbols by volume: {e}")

        if not symbols:
            logger_main.error(f"No symbols passed pre-filtering for {exchange_id}, stopping")
            return []

        # Initialize cache for invalid symbols
        invalid_symbols = await cache.get_invalid_symbols(exchange_id) or set()
        logger_main.info(f"Loaded {len(invalid_symbols)} invalid symbols from cache: {list(invalid_symbols)[:5]}...")

        # Analyze market conditions for dynamic thresholds
        market_conditions = await analyze_market_conditions(exchange_id, user_id, timeframe='1h', limit=100, testnet=testnet, exchange=exchange)
        if market_conditions:
            market_volatility = market_conditions['market_volatility']
            market_volume = market_conditions['market_volume']
            # Динамические пороговые значения
            min_volume_threshold = max(10, market_volume * 0.05)  # Сниженный порог: 5% от среднего объёма
            min_volatility_threshold = max(0.01, market_volatility * 0.2)  # Сниженный порог: 20% от волатильности рынка
        else:
            min_volume_threshold = 10  # Сниженный порог
            min_volatility_threshold = 0.01  # Сниженный порог

        logger_main.info(f"Using dynamic thresholds: min_volume_threshold={min_volume_threshold}, min_volatility_threshold={min_volatility_threshold}%")

        # Filter symbols based on volatility, signals, and trading activity
        valid_symbols = []
        timeframe = '1h'  # Timeframe for analysis
        limit = 100  # Number of candles for analysis

        # Process symbols in batches to speed up filtering
        batch_size = 50  # Increased batch size for better performance
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            logger_main.info(f"Processing batch {i//batch_size + 1} of {len(symbols)//batch_size + 1} (symbols {i} to {min(i + batch_size, len(symbols))})")
            tasks = []
            for symbol in batch:
                # Skip if symbol is already known to be invalid
                if symbol in invalid_symbols:
                    logger_main.debug(f"Symbol {symbol} is in invalid symbols cache, skipping")
                    continue

                tasks.append(asyncio.create_task(filter_symbol(
                    exchange_id, user_id, symbol, testnet, exchange,
                    min_volume_threshold, min_volatility_threshold,
                    timeframe, limit, cache, invalid_symbols
                )))

            # Wait for batch to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for symbol, result in zip(batch, results):
                if isinstance(result, Exception):
                    logger_main.debug(f"Error processing symbol {symbol}: {result}, adding to invalid cache")
                    invalid_symbols.add(symbol)
                    await cache.cache_invalid_symbol(exchange_id, symbol)
                    continue
                if result:
                    valid_symbols.append(symbol)
                    logger_main.debug(f"Symbol {symbol} passed filtering and added to valid symbols")

        if not valid_symbols:
            logger_main.error(f"No valid symbols found after filtering for {exchange_id}, stopping")
            return []

        logger_main.info(f"Fetched {len(valid_symbols)} test symbols for {exchange_id}: {valid_symbols[:5]}...")
        return valid_symbols

    except Exception as e:
        logger_main.error(f"Error fetching test symbols for {exchange_id}: {e}")
        return []
    finally:
        if exchange is not None:
            logger_main.info(f"Closing exchange connection for {exchange_id}")
            await exchange.close()
        else:
            logger_main.warning(f"No exchange instance to close for {exchange_id}")

async def filter_symbol(exchange_id, user_id, symbol, testnet, exchange, min_volume_threshold, min_volatility_threshold, timeframe, limit, cache, invalid_symbols):
    """Filters a single symbol based on volatility, signals, and trading activity."""
    try:
        logger_main.debug(f"Validating symbol {symbol}")
        if not await asyncio.wait_for(validate_symbol(exchange_id, user_id, symbol, testnet=testnet, exchange=exchange), timeout=10):
            logger_main.debug(f"Symbol {symbol} failed validation in validate_symbol")
            return False

        # Analyze token (volatility and volume)
        analysis = await analyze_token(exchange_id, user_id, symbol, timeframe=timeframe, limit=limit, testnet=testnet, exchange=exchange)
        if not analysis:
            logger_main.debug(f"Failed to analyze token {symbol}")
            return False

        volume = analysis.get('total_volume', 0)
        volatility = analysis.get('volatility', 0)
        if volume < min_volume_threshold:
            logger_main.debug(f"Symbol {symbol} has low volume ({volume} < {min_volume_threshold})")
            return False
        if volatility < min_volatility_threshold:
            logger_main.debug(f"Symbol {symbol} has low volatility ({volatility} < {min_volatility_threshold}%)")
            return False

        # Fetch OHLCV data for signal generation
        ohlcv_data = await fetch_ohlcv(exchange_id, symbol, user_id, timeframe=timeframe, limit=limit, testnet=testnet, exchange=exchange)
        if ohlcv_data is None or ohlcv_data.empty:
            logger_main.debug(f"Failed to fetch OHLCV data for {symbol}")
            return False

        # Calculate RSI (for logging purposes)
        rsi = calculate_rsi(ohlcv_data['close'])
        if rsi is None:
            logger_main.debug(f"Failed to calculate RSI for {symbol}")
            return False

        latest_rsi = rsi.iloc[-1]
        # Temporarily disable signal filter to allow more symbols to pass
        # signal = await generate_dynamic_signals(exchange_id, user_id, symbol, timeframe, limit, testnet, exchange)
        # if signal is None:
        #     logger_main.debug(f"No trading signal for {symbol} (RSI: {latest_rsi})")
        #     return False

        logger_main.debug(f"Symbol {symbol} passed filtering (volume: {volume}, volatility: {volatility}%, RSI: {latest_rsi})")
        return True
    except Exception as e:
        logger_main.debug(f"Error filtering symbol {symbol}: {e}")
        return False

__all__ = ['get_test_symbols']
