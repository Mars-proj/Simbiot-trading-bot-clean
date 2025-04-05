import asyncio
import pandas as pd
from logging_setup import logger_main
from market_analyzer import MarketAnalyzer
from market_rentgen_core import MarketRentgenCore
import time
from historical_data_fetcher import fetch_historical_data
from cache_manager import load_symbol_cache

async def analyze_market_state(exchange_pool, exchange_id):
    """Analyzes the current market state (trending, sideways, etc.) using major symbols as a reference."""
    logger_main.info("Analyzing market state")
    exchange = await exchange_pool.get_exchange(exchange_id, "user1", testnet=False)
    if not exchange:
        logger_main.error("Failed to get exchange instance for market state analysis")
        return "unknown"

    try:
        # List of major symbols to try for market state analysis
        major_symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]  # Use format without slash
        ohlcv = None
        used_symbol = None

        # Fetch historical data for major symbols (last 90 days)
        since = int(time.time()) - 90 * 24 * 60 * 60  # 90 days ago
        for symbol in major_symbols:
            logger_main.debug(f"Fetching historical data for {symbol} with since={since}")
            ohlcv = await fetch_historical_data(exchange_id, "user1", symbol, since, testnet=False, exchange=exchange, limit=2000)
            if ohlcv:
                used_symbol = symbol
                logger_main.debug(f"Fetched {len(ohlcv)} OHLCV data points for {symbol}")
                break
            else:
                logger_main.error(f"Failed to fetch historical data for {symbol}")

        if not ohlcv:
            logger_main.error("Failed to fetch historical data for all major symbols (BTCUSDT, ETHUSDT, BNBUSDT)")
            return "unknown"

        # Convert to DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        logger_main.debug(f"Converted OHLCV data to DataFrame with {len(df)} rows")

        # Initialize market analyzer
        market_analyzer = MarketAnalyzer()
        market_analyzer.load_data(ohlcv)
        logger_main.debug("Loaded OHLCV data into MarketAnalyzer")

        # Calculate volatility (last 14 days)
        volatility = market_analyzer.calculate_volatility(window=14)
        if volatility is None:
            logger_main.warning("Failed to calculate market volatility")
            return "unknown"
        logger_main.debug(f"Calculated volatility: {volatility:.2%}")

        # Detect trend (last 20 days)
        trend = market_analyzer.detect_trend(window=20)
        if trend is None:
            logger_main.warning("Failed to detect market trend")
            return "unknown"
        logger_main.debug(f"Detected trend: {trend}")

        # Determine market state
        if volatility > 0.3:  # High volatility
            if trend in ['up', 'down']:
                market_state = "trending_high_volatility"
            else:
                market_state = "sideways_high_volatility"
        else:  # Low volatility
            if trend in ['up', 'down']:
                market_state = "trending_low_volatility"
            else:
                market_state = "sideways_low_volatility"

        logger_main.info(f"Market state: {market_state} (volatility={volatility:.2%}, trend={trend})")
        return market_state

    except Exception as e:
        logger_main.error(f"Error analyzing market state: {e}\n{traceback.format_exc()}")
        return "unknown"

async def calculate_dynamic_thresholds(exchange_pool, exchange_id, backtest_results, market_state):
    """Calculates dynamic thresholds based on all backtest results, market data, and market state."""
    logger_main.info(f"Calculating dynamic thresholds for market state: {market_state}")
    exchange = await exchange_pool.get_exchange(exchange_id, "user1", testnet=False)
    if not exchange:
        logger_main.error("Failed to get exchange instance for dynamic threshold calculation")
        return {"min_profit": 0.005, "min_volatility": 0.1, "min_sentiment": 0.5, "volume_spike_threshold": 1.5}

    # Load working symbols to filter backtest results
    working_cache = await load_symbol_cache("working_symbols.json")
    logger_main.debug(f"Loaded working symbols cache: {working_cache}")
    working_symbols = set(working_cache['symbols'])
    logger_main.debug(f"Loaded {len(working_symbols)} working symbols for threshold calculation: {list(working_symbols)[:5]}...")

    # Sample a subset of symbols for threshold calculation (limit to 100 symbols, only those in working_symbols)
    all_symbols = list(backtest_results.keys())
    logger_main.debug(f"All symbols from backtest_results: {len(all_symbols)} symbols, first 5: {all_symbols[:5]}...")
    sampled_symbols = [symbol for symbol in all_symbols[:100] if symbol in working_symbols]
    logger_main.info(f"Sampled {len(sampled_symbols)} symbols for threshold calculation: {sampled_symbols[:5]}...")

    if not sampled_symbols:
        logger_main.warning("No valid symbols available for threshold calculation after filtering with working symbols")
        return {"min_profit": 0.005, "min_volatility": 0.1, "min_sentiment": 0.5, "volume_spike_threshold": 1.5}

    ohlcv_data = {}
    batch_size = 20
    for i in range(0, len(sampled_symbols), batch_size):
        batch = sampled_symbols[i:i + batch_size]
        logger_main.info(f"Fetching historical data for batch {i//batch_size + 1} of {len(sampled_symbols)//batch_size + 1}")
        tasks = []
        for symbol in batch:
            since = int(time.time()) - 90 * 24 * 60 * 60  # 90 days ago
            tasks.append(asyncio.create_task(fetch_historical_data(exchange_id, "user1", symbol, since, testnet=False, exchange=exchange, limit=2000)))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for symbol, result in zip(batch, results):
            if isinstance(result, Exception):
                logger_main.warning(f"Failed to fetch historical data for {symbol}: {result}")
                continue
            if result:
                ohlcv_data[symbol] = result
                logger_main.info(f"Successfully fetched {len(result)} OHLCV data points for {symbol}")

    # Initialize analyzers
    market_analyzer = MarketAnalyzer()
    market_rentgen = MarketRentgenCore()
    profits = []
    volatilities = []
    sentiments = []

    for symbol, ohlcv in ohlcv_data.items():
        if ohlcv:
            market_analyzer.load_data(ohlcv)
            market_rentgen.load_data(ohlcv)
            result = backtest_results.get(symbol)
            if result and isinstance(result, dict) and 'profit' in result:
                profits.append(result['profit'])
            volatility = market_analyzer.calculate_volatility(window=10)
            if volatility is not None:
                volatilities.append(volatility)
            sentiment = market_rentgen.calculate_market_sentiment()
            if sentiment is not None:
                sentiments.append(sentiment)

    # Calculate dynamic thresholds based on market state
    min_profit = pd.Series(profits).quantile(0.25) if profits else 0.005  # 25th percentile
    min_volatility = pd.Series(volatilities).quantile(0.25) if volatilities else 0.1  # 25th percentile
    min_sentiment = pd.Series(sentiments).mean() if sentiments else 0.5  # Mean sentiment
    volume_spike_threshold = pd.Series(volatilities).quantile(0.75) / pd.Series(volatilities).mean() if volatilities and pd.Series(volatilities).mean() > 0 else 1.5  # 75th percentile relative to mean

    # Adjust thresholds based on market state
    if "high_volatility" in market_state:
        min_volatility = max(min_volatility * 1.5, 0.3)  # Higher volatility threshold for trending markets
        volume_spike_threshold = max(volume_spike_threshold * 1.2, 1.8)  # Higher volume spike threshold
        min_sentiment = max(min_sentiment * 0.9, 0.4)  # Slightly lower sentiment threshold
    elif "sideways" in market_state:
        min_volatility = max(min_volatility * 0.5, 0.05)  # Lower volatility threshold for sideways markets
        volume_spike_threshold = max(volume_spike_threshold * 0.8, 1.2)  # Lower volume spike threshold
        min_sentiment = max(min_sentiment * 1.1, 0.6)  # Higher sentiment threshold for stability

    logger_main.info(f"Dynamic thresholds calculated: min_profit={min_profit:.4f}, min_volatility={min_volatility:.4f}, min_sentiment={min_sentiment:.4f}, volume_spike_threshold={volume_spike_threshold:.4f}")
    await exchange_pool.close_exchange(exchange_id, "user1")
    return {
        "min_profit": max(min_profit, 0.001),
        "min_volatility": min_volatility,
        "min_sentiment": min_sentiment,
        "volume_spike_threshold": volume_spike_threshold
    }
