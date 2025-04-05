import asyncio
import pandas as pd
import time
from logging_setup import logger_main
from market_analyzer import MarketAnalyzer
from market_rentgen_core import MarketRentgenCore
from historical_data_fetcher import fetch_historical_data
from cache_manager import load_symbol_cache, save_symbol_cache

async def categorize_symbols(symbols, backtest_results, market_state, ohlcv_data):
    """Categorizes symbols based on market state and their characteristics."""
    logger_main.info(f"Categorizing {len(symbols)} symbols based on market state: {market_state}")
    categories = {
        "high_volatility": [],
        "low_volatility": [],
        "trending": [],
        "sideways": [],
        "high_sentiment": [],
        "low_sentiment": []
    }

    market_analyzer = MarketAnalyzer()
    market_rentgen = MarketRentgenCore()

    for symbol in symbols:
        try:
            ohlcv = ohlcv_data.get(symbol)
            if not ohlcv:
                logger_main.warning(f"No OHLCV data for {symbol}, skipping categorization")
                continue

            market_analyzer.load_data(ohlcv)
            market_rentgen.load_data(ohlcv)

            volatility = market_analyzer.calculate_volatility(window=10)
            trend = market_analyzer.detect_trend(window=10)
            sentiment = market_rentgen.calculate_market_sentiment()

            if volatility is None or trend is None or sentiment is None:
                logger_main.warning(f"Failed to analyze {symbol} (volatility={volatility}, trend={trend}, sentiment={sentiment}), skipping")
                continue

            # Categorize by volatility
            if volatility > 0.3:
                categories["high_volatility"].append(symbol)
            else:
                categories["low_volatility"].append(symbol)

            # Categorize by trend
            if trend in ['up', 'down']:
                categories["trending"].append(symbol)
            else:
                categories["sideways"].append(symbol)

            # Categorize by sentiment
            if sentiment > 0.6:
                categories["high_sentiment"].append(symbol)
            else:
                categories["low_sentiment"].append(symbol)

            logger_main.debug(f"Categorized {symbol}: volatility={volatility:.2%}, trend={trend}, sentiment={sentiment:.2%}")

        except Exception as e:
            logger_main.error(f"Error categorizing symbol {symbol}: {e}")
            continue

    # Select symbols based on market state
    selected_symbols = []
    if "high_volatility" in market_state:
        selected_symbols.extend(categories["high_volatility"])
        selected_symbols.extend(categories["trending"])
    elif "sideways" in market_state:
        selected_symbols.extend(categories["low_volatility"])
        selected_symbols.extend(categories["sideways"])
    else:
        # Default: mix of trending and high sentiment
        selected_symbols.extend(categories["trending"])
        selected_symbols.extend(categories["high_sentiment"])

    # Remove duplicates while preserving order
    selected_symbols = list(dict.fromkeys(selected_symbols))
    logger_main.info(f"Selected {len(selected_symbols)} symbols for trading based on market state: {selected_symbols[:5]}...")
    return selected_symbols

async def filter_symbols(symbols, backtest_results, user_id, exchange_pool, exchange_id, dynamic_thresholds, market_state):
    """Filters symbols based on backtest results, dynamic market analysis, and market state."""
    valid_symbols = []
    skipped_symbols = []  # Store symbols that pass profit threshold but fail data fetch
    total_symbols = len(symbols)  # Total number of symbols passed to the function
    logger_main.info(f"Starting symbol filtering for {total_symbols} symbols with dynamic thresholds and market state: {market_state}")

    # Initialize market analysis tools
    market_analyzer = MarketAnalyzer()
    market_rentgen = MarketRentgenCore()

    # Fetch historical data for market analysis
    exchange = await exchange_pool.get_exchange(exchange_id, user_id, testnet=False)
    if not exchange:
        logger_main.error(f"Failed to get exchange instance for {exchange_id}:{user_id}")
        return []

    # Load cached symbol lists
    problematic_cache = await load_symbol_cache("problematic_symbols.json")
    working_cache = await load_symbol_cache("working_symbols.json")
    problematic_symbols = problematic_cache['symbols']
    working_symbols = working_cache['symbols']
    logger_main.debug(f"Loaded {len(problematic_symbols)} problematic symbols and {len(working_symbols)} working symbols")

    # Check if symbol lists need to be updated (once every 24 hours)
    current_time = time.time()
    cache_is_stale = (current_time - problematic_cache['timestamp'] > 24 * 60 * 60) or (current_time - working_cache['timestamp'] > 24 * 60 * 60)
    ohlcv_data = {}

    if cache_is_stale:
        logger_main.info("Symbol caches are stale, reprocessing all symbols with CoinGecko")
        problematic_symbols = set()
        working_symbols = set()
        batch_size = 50  # Increased batch size for faster processing
        since = int(current_time) - 90 * 24 * 60 * 60  # 90 days ago
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            logger_main.info(f"Fetching historical data from CoinGecko for batch {i//batch_size + 1} of {len(symbols)//batch_size + 1}")
            tasks = []
            for symbol in batch:
                tasks.append(asyncio.create_task(fetch_historical_data(exchange_id, user_id, symbol, since, testnet=False, exchange=exchange, limit=2000)))
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for symbol, result in zip(batch, results):
                if isinstance(result, Exception) or result is None:
                    problematic_symbols.add(symbol)
                    logger_main.warning(f"Added {symbol} to problematic symbols")
                else:
                    working_symbols.add(symbol)
                    ohlcv_data[symbol] = result
                    logger_main.info(f"Added {symbol} to working symbols with {len(result)} OHLCV data points")

        # Save updated caches
        await save_symbol_cache("problematic_symbols.json", {'timestamp': int(current_time), 'symbols': list(problematic_symbols)})
        await save_symbol_cache("working_symbols.json", {'timestamp': int(current_time), 'symbols': list(working_symbols)})
    else:
        logger_main.info(f"Using cached symbol lists with {len(working_symbols)} working symbols, fetching historical data")
        since = int(current_time) - 90 * 24 * 60 * 60  # 90 days ago
        # Parallel fetching of historical data for all working symbols
        tasks = []
        for symbol in working_symbols:
            logger_main.debug(f"Queuing fetch for {symbol}")
            tasks.append(asyncio.create_task(fetch_historical_data(exchange_id, user_id, symbol, since, testnet=False, exchange=exchange, limit=2000)))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for symbol, result in zip(working_symbols.copy(), results):  # Use copy to avoid RuntimeError
            if isinstance(result, Exception) or result is None:
                problematic_symbols.add(symbol)
                working_symbols.discard(symbol)  # Use discard to avoid KeyError
                logger_main.warning(f"Moved {symbol} from working to problematic symbols: {result}")
            else:
                ohlcv_data[symbol] = result
                logger_main.info(f"Fetched {len(result)} OHLCV data points for {symbol}")

        # Save updated caches after fetching new data
        await save_symbol_cache("problematic_symbols.json", {'timestamp': int(current_time), 'symbols': list(problematic_symbols)})
        await save_symbol_cache("working_symbols.json", {'timestamp': int(current_time), 'symbols': list(working_symbols)})

    # Get active symbols from the exchange
    try:
        markets = await exchange.fetch_markets()
        active_symbols = {market['symbol'] for market in markets if market.get('active', True)}
        logger_main.info(f"Fetched {len(active_symbols)} active symbols from exchange")
    except Exception as e:
        logger_main.error(f"Failed to fetch markets: {e}")
        active_symbols = set(symbols)

    # Filter working symbols to only include those that are tradable on the exchange
    tradable_symbols = [symbol for symbol in working_symbols if symbol in active_symbols]
    logger_main.info(f"Found {len(tradable_symbols)} tradable symbols: {tradable_symbols[:5]}...")

    # Categorize tradable symbols based on market state
    categorized_symbols = await categorize_symbols(tradable_symbols, backtest_results, market_state, ohlcv_data)

    # Process categorized symbols
    for symbol in categorized_symbols:
        try:
            if symbol not in backtest_results:
                logger_main.warning(f"Symbol {symbol} not found in backtest_results for user {user_id}, skipping")
                continue
            result = backtest_results.get(symbol)
            if result is None:
                logger_main.warning(f"No backtest result for {symbol} for user {user_id}, skipping")
                continue
            if not isinstance(result, dict) or 'profit' not in result:
                logger_main.error(f"Invalid backtest result for {symbol}: {result}")
                continue
            profit = result.get('profit', 0)
            if not isinstance(profit, (int, float)):
                logger_main.error(f"Profit for {symbol} is not a number: {profit}")
                continue
            if profit < dynamic_thresholds['min_profit']:
                logger_main.warning(f"Backtest profit for {symbol} ({profit:.2%}) is below dynamic threshold ({dynamic_thresholds['min_profit']:.2%}), skipping")
                continue

            ohlcv = ohlcv_data.get(symbol)
            if not ohlcv:
                logger_main.warning(f"No historical data for {symbol}, adding to skipped symbols")
                skipped_symbols.append((symbol, profit))
                continue

            # Load data into market analysis tools
            market_analyzer.load_data(ohlcv)
            market_rentgen.load_data(ohlcv)

            # Analyze volatility
            volatility = market_analyzer.calculate_volatility(window=10)
            if volatility is None:
                logger_main.warning(f"Failed to calculate volatility for {symbol}, skipping")
                continue
            if volatility < dynamic_thresholds['min_volatility']:
                logger_main.warning(f"Volatility for {symbol} ({volatility:.2%}) is below dynamic threshold ({dynamic_thresholds['min_volatility']:.2%}), skipping")
                continue

            # Detect trend
            trend = market_analyzer.detect_trend(window=10)
            if trend is None:
                logger_main.warning(f"Failed to detect trend for {symbol}, skipping")
                continue

            # Analyze volume spikes
            volume_spike = market_rentgen.analyze_volume_spikes(threshold=dynamic_thresholds['volume_spike_threshold'])
            if volume_spike is None:
                logger_main.warning(f"Failed to analyze volume spikes for {symbol}, skipping")
                continue
            if len(ohlcv) < 100 and not volume_spike:
                logger_main.debug(f"Insufficient data for {symbol}, allowing without volume spike")
            elif not volume_spike:
                logger_main.warning(f"No recent volume spike for {symbol} above threshold {dynamic_thresholds['volume_spike_threshold']}, skipping")
                continue

            # Calculate market sentiment
            sentiment = market_rentgen.calculate_market_sentiment()
            if sentiment is None:
                logger_main.warning(f"Failed to calculate market sentiment for {symbol}, skipping")
                continue
            if sentiment < dynamic_thresholds['min_sentiment']:
                logger_main.warning(f"Market sentiment for {symbol} ({sentiment:.2%}) is below dynamic threshold ({dynamic_thresholds['min_sentiment']:.2%}), skipping")
                continue

            valid_symbols.append(symbol)
            logger_main.info(f"Symbol {symbol} passed all filters for user {user_id}: profit={profit:.2%}, volatility={volatility:.2%}, trend={trend}, volume_spike={volume_spike}, sentiment={sentiment:.2%}")

            if len(valid_symbols) >= 10:  # Stop early if we have enough symbols
                logger_main.info("Found sufficient symbols, stopping filter early")
                break

        except Exception as e:
            logger_main.error(f"Error processing symbol {symbol} for user {user_id}: {e}")
            continue

    logger_main.info(f"Completed symbol filtering, found {len(valid_symbols)} valid symbols")
    # Ensure minimum number of symbols (e.g., 10) for trading
    if len(valid_symbols) < 10:
        logger_main.warning(f"Only {len(valid_symbols)} symbols found, supplementing with top performers from skipped symbols")
        # Sort skipped symbols by profit and take enough to reach 10
        skipped_symbols.sort(key=lambda x: x[1], reverse=True)
        needed = 10 - len(valid_symbols)
        additional_symbols = [s for s, _ in skipped_symbols[:needed]]
        valid_symbols.extend(additional_symbols)
        logger_main.info(f"Added {len(additional_symbols)} symbols from skipped list: {additional_symbols}")

    if not valid_symbols:
        logger_main.warning("No symbols passed filters, using top 10 by profit from backtest")
        valid_symbols = sorted([(s, backtest_results[s]['profit']) for s in backtest_results if backtest_results[s] and 'profit' in backtest_results[s]], key=lambda x: x[1], reverse=True)[:10]
        valid_symbols = [s for s, _ in valid_symbols]
    return valid_symbols
