print("Starting imports in main.py")

print("Importing asyncio")
import asyncio
print("Imported asyncio")

print("Importing json")
import json
print("Imported json")

print("Importing os")
import os
print("Imported os")

print("Importing pandas")
import pandas as pd
print("Imported pandas")

print("Importing from logging_setup")
from logging_setup import logger_main
print("Imported from logging_setup")

print("Importing from start_trading_all")
from start_trading_all import start_trading_all, run_backtest
print("Imported from start_trading_all")

print("Importing from bot_user_data")
from bot_user_data import BotUserData
print("Imported from bot_user_data")

print("Importing from test_symbols")
from test_symbols import get_test_symbols
print("Imported from test_symbols")

print("Importing from trade_pool_manager")
from trade_pool_manager import schedule_trade_pool_cleanup
print("Imported from trade_pool_manager")

print("Importing from position_monitor")
from position_monitor import monitor_positions
print("Imported from position_monitor")

print("Importing from retraining_manager")
from retraining_manager import RetrainingManager
print("Imported from retraining_manager")

print("Importing from exchange_pool")
from exchange_pool import ExchangePool
print("Imported from exchange_pool")

print("Importing from cache_utils")
from cache_utils import RedisClient
print("Imported from cache_utils")

print("Importing from market_analyzer")
from market_analyzer import MarketAnalyzer
print("Imported from market_analyzer")

print("Importing from market_rentgen_core")
from market_rentgen_core import MarketRentgenCore
print("Imported from market_rentgen_core")

print("Importing time")
import time
print("Imported time")

print("Importing traceback")
import traceback
print("Imported traceback")

async def main():
    """Main entry point for the trading bot system."""
    try:
        logger_main.info("Starting main function")
        # Configuration
        exchange_id = "mexc"  # Use MEXC for real trading
        users = [
            {"user_id": "user1", "testnet": False},
            {"user_id": "user2", "testnet": False},
            {"user_id": "user3", "testnet": False},
        ]
        model_path = "models/trading_model.pth"  # Example model path
        backtest_days = 7  # Reduced number of days for backtest (was 30)

        logger_main.info(f"Configuration: exchange_id={exchange_id}, users={users}, model_path={model_path}, backtest_days={backtest_days}")

        # Process all users asynchronously
        logger_main.info("Calling process_users")
        await process_users(users, exchange_id, model_path, backtest_days)
        logger_main.info("Finished process_users")

    except Exception as e:
        logger_main.error(f"Error in main loop: {e}\n{traceback.format_exc()}")

async def process_users(users, exchange_id, model_path, backtest_days):
    """Processes trading for all users asynchronously."""
    exchange_pool = ExchangePool()
    try:
        logger_main.info("Starting process_users")
        # Check if selected pairs file exists
        selected_pairs_file = "selected_pairs.json"
        logger_main.info(f"Checking for selected pairs file: {selected_pairs_file}")
        if os.path.exists(selected_pairs_file):
            logger_main.info("Selected pairs file exists, loading symbols")
            with open(selected_pairs_file, 'r') as f:
                symbols = json.load(f)
            logger_main.info(f"Loaded {len(symbols)} selected pairs from {selected_pairs_file}: {symbols[:5]}...")
        else:
            logger_main.info("Selected pairs file does not exist, fetching test symbols")
            # Fetch test symbols for the first user
            first_user = users[0]
            user_id = first_user['user_id']
            testnet = first_user['testnet']
            logger_main.info(f"Fetching test symbols for user {user_id} (will be saved to {selected_pairs_file})")
            symbols = await get_test_symbols(exchange_pool, exchange_id, user_id, testnet=testnet)
            if not symbols:
                logger_main.error(f"No valid symbols found for trading, stopping")
                return
            # Save the selected pairs to a file
            with open(selected_pairs_file, 'w') as f:
                json.dump(symbols, f)
            logger_main.info(f"Saved {len(symbols)} selected pairs to {selected_pairs_file}: {symbols[:5]}...")

        # Check if backtest results file exists
        backtest_results_file = "backtest_results.json"
        logger_main.info(f"Checking for backtest results file: {backtest_results_file}")
        if os.path.exists(backtest_results_file):
            logger_main.info("Backtest results file exists, loading results")
            try:
                with open(backtest_results_file, 'r') as f:
                    backtest_results = json.load(f)
                logger_main.info(f"Loaded backtest results for {len(backtest_results)} symbols from {backtest_results_file}")
                logger_main.debug(f"Backtest results structure: {backtest_results}")
            except Exception as e:
                logger_main.error(f"Failed to load backtest results from {backtest_results_file}: {e}\n{traceback.format_exc()}")
                backtest_results = None
        else:
            logger_main.info("Backtest results file does not exist, running backtest")
            # Run backtest for all symbols (once for all users)
            first_user = users[0]
            user_id = first_user['user_id']
            testnet = first_user['testnet']
            logger_main.info(f"Running backtest for all symbols (will be cached for all users)")
            backtest_results = await run_backtests(exchange_id, user_id, symbols, backtest_days, testnet)
            logger_main.info(f"Backtest completed, results: {len(backtest_results)} symbols")
            # Save backtest results to a file
            with open(backtest_results_file, 'w') as f:
                json.dump(backtest_results, f)
            logger_main.info(f"Saved backtest results for {len(backtest_results)} symbols to {backtest_results_file}")
            logger_main.debug(f"Backtest results structure after backtest: {backtest_results}")

        # Debug: Check if backtest_results is None or empty
        if backtest_results is None:
            logger_main.error("Backtest results are None, cannot proceed with trading")
            return
        if not backtest_results:
            logger_main.error("Backtest results are empty, cannot proceed with trading")
            return

        # Calculate dynamic thresholds based on all backtest results
        dynamic_thresholds = await calculate_dynamic_thresholds(exchange_pool, exchange_id, backtest_results)

        # Process each user with the backtest results
        logger_main.info("Processing users with backtest results")
        tasks = []
        for user in users:
            logger_main.info(f"Starting processing for user {user['user_id']}")
            try:
                task = asyncio.create_task(run_trading_for_user(
                    user, exchange_id, model_path, backtest_days, exchange_pool, symbols, backtest_results, dynamic_thresholds
                ))
                tasks.append(task)
            except Exception as e:
                logger_main.error(f"Error creating task for user {user['user_id']}: {e}\n{traceback.format_exc()}")
                continue
        logger_main.info(f"Created {len(tasks)} tasks for processing users")

        # Wait for all tasks to complete and handle exceptions
        logger_main.debug("Waiting for all tasks to complete")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for idx, (user, result) in enumerate(zip(users, results)):
            if isinstance(result, Exception):
                logger_main.error(f"Task {idx} for user {user['user_id']} failed with exception: {result}\n{traceback.format_exc()}")
            else:
                logger_main.info(f"Task {idx} for user {user['user_id']} completed successfully with result: {result}")
    except Exception as e:
        logger_main.error(f"Error in process_users: {e}\n{traceback.format_exc()}")
        raise  # Добавляем raise, чтобы увидеть полный стек вызовов
    finally:
        logger_main.info("Closing all exchange instances in ExchangePool")
        await exchange_pool.close_all()

async def calculate_dynamic_thresholds(exchange_pool, exchange_id, backtest_results):
    """Calculates dynamic thresholds based on backtest results and market data."""
    logger_main.info("Calculating dynamic thresholds")
    exchange = await exchange_pool.get_exchange(exchange_id, "user1", testnet=False)
    if not exchange:
        logger_main.error("Failed to get exchange instance for dynamic threshold calculation")
        return {"min_profit": 0.005, "min_volatility": 0.1, "min_sentiment": 0.5, "volume_spike_threshold": 1.5}

    # Sample a subset of symbols for threshold calculation
    sampled_symbols = list(backtest_results.keys())[:100]  # Use first 100 symbols
    ohlcv_data = {}
    for symbol in sampled_symbols:
        since = int(time.time()) - 90 * 24 * 60 * 60  # 90 days ago
        from historical_data_fetcher import fetch_historical_data
        ohlcv = await fetch_historical_data(exchange_id, "user1", symbol, since, testnet=False, exchange=exchange, limit=2000)
        if ohlcv:
            ohlcv_data[symbol] = ohlcv
            logger_main.info(f"Successfully fetched {len(ohlcv)} OHLCV data points for {symbol}")

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
            volatility = market_analyzer.calculate_volatility(window=14)
            if volatility is not None:
                volatilities.append(volatility)
            sentiment = market_rentgen.calculate_market_sentiment()
            if sentiment is not None:
                sentiments.append(sentiment)

    # Calculate dynamic thresholds
    min_profit = pd.Series(profits).quantile(0.25) if profits else 0.005  # 25th percentile
    min_volatility = pd.Series(volatilities).quantile(0.25) if volatilities else 0.1  # 25th percentile
    min_sentiment = pd.Series(sentiments).mean() if sentiments else 0.5  # Mean sentiment
    volume_spike_threshold = pd.Series(volatilities).quantile(0.75) / pd.Series(volatilities).mean() if volatilities and pd.Series(volatilities).mean() > 0 else 1.5  # 75th percentile relative to mean

    logger_main.info(f"Dynamic thresholds calculated: min_profit={min_profit:.4f}, min_volatility={min_volatility:.4f}, min_sentiment={min_sentiment:.4f}, volume_spike_threshold={volume_spike_threshold:.4f}")
    await exchange_pool.close_exchange(exchange_id, "user1")
    return {
        "min_profit": max(min_profit, 0.001),  # Minimum safety threshold
        "min_volatility": max(min_volatility, 0.05),
        "min_sentiment": max(min_sentiment, 0.4),
        "volume_spike_threshold": max(volume_spike_threshold, 1.2)
    }

async def run_backtests(exchange_id, user_id, symbols, backtest_days, testnet):
    """Runs backtests for all symbols in parallel and returns results."""
    backtest_results = {}
    batch_size = 10  # Process 10 symbols at a time
    logger_main.info(f"Starting backtest for {len(symbols)} symbols in batches of {batch_size}")
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        logger_main.info(f"Processing backtest batch {i//batch_size + 1} of {len(symbols)//batch_size + 1} (symbols {i} to {min(i + batch_size, len(symbols))})")
        tasks = []
        for symbol in batch:
            tasks.append(asyncio.create_task(run_backtest(
                exchange_id, user_id, symbol,
                days=backtest_days,
                leverage=1.0,
                trade_percentage=0.1,
                rsi_overbought=70,
                rsi_oversold=30,
                test_mode=testnet
            )))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for symbol, result in zip(batch, results):
            if isinstance(result, Exception):
                logger_main.warning(f"Backtest failed for {symbol}: {result}")
                backtest_results[symbol] = None
            else:
                backtest_results[symbol] = result
                logger_main.debug(f"Backtest result for {symbol}: {result}")
    logger_main.info(f"Backtest completed for {len(backtest_results)} symbols")
    return backtest_results

async def filter_symbols(symbols, backtest_results, user_id, exchange_pool, exchange_id, dynamic_thresholds):
    """Filters symbols based on backtest results and dynamic market analysis."""
    valid_symbols = []
    logger_main.info(f"Starting symbol filtering for {len(symbols)} symbols with dynamic thresholds")
    # Debug: Log the entire backtest_results to see its structure
    logger_main.debug(f"Backtest results structure: {backtest_results}")
    logger_main.debug(f"Dynamic thresholds: {dynamic_thresholds}")

    # Initialize market analysis tools
    market_analyzer = MarketAnalyzer()
    market_rentgen = MarketRentgenCore()

    # Fetch historical data for market analysis
    exchange = await exchange_pool.get_exchange(exchange_id, user_id, testnet=False)
    if not exchange:
        logger_main.error(f"Failed to get exchange instance for {exchange_id}:{user_id}")
        return []

    for idx, symbol in enumerate(symbols):
        logger_main.debug(f"Processing symbol {idx}/{len(symbols)}: {symbol}, type: {type(symbol)}")
        try:
            # Additional debug logging
            logger_main.debug(f"Checking if symbol {symbol} exists in backtest_results")
            if symbol not in backtest_results:
                logger_main.warning(f"Symbol {symbol} not found in backtest_results for user {user_id}, skipping")
                continue
            logger_main.debug(f"Attempting to access backtest_results for symbol: {symbol}")
            logger_main.debug(f"Backtest results keys before access: {list(backtest_results.keys())[:5]}...")
            logger_main.debug(f"Backtest results type: {type(backtest_results)}")
            logger_main.debug(f"Backtest results length: {len(backtest_results)}")
            logger_main.debug(f"Backtest results content for {symbol}: {backtest_results.get(symbol)}")
            result = backtest_results.get(symbol)
            logger_main.debug(f"Backtest result for {symbol}: {result}, type: {type(result)}")
            if result is None:
                logger_main.warning(f"No backtest result for {symbol} for user {user_id}, skipping")
                continue
            # Additional debug logging
            logger_main.debug(f"Attempting to access 'profit' in result: {result}")
            if not isinstance(result, dict):
                logger_main.error(f"Backtest result for {symbol} is not a dictionary: {result}")
                continue
            if 'profit' not in result:
                logger_main.error(f"Key 'profit' not found in backtest result for {symbol}: {result}")
                continue
            profit = result.get('profit', 0)
            logger_main.debug(f"Backtest profit for {symbol}: {profit}, type: {type(profit)}")
            if not isinstance(profit, (int, float)):
                logger_main.error(f"Profit for {symbol} is not a number: {profit}, type: {type(profit)}")
                continue
            logger_main.debug(f"Backtest profit for {symbol}: {profit:.2%}, threshold: {dynamic_thresholds['min_profit']:.2%}")
            if profit < dynamic_thresholds['min_profit']:
                logger_main.warning(f"Backtest profit for {symbol} ({profit:.2%}) is below dynamic threshold ({dynamic_thresholds['min_profit']:.2%}), skipping")
                continue

            # Fetch historical data for market analysis
            since = int(time.time()) - 90 * 24 * 60 * 60  # 90 days ago
            from historical_data_fetcher import fetch_historical_data
            ohlcv = await fetch_historical_data(exchange_id, user_id, symbol, since, testnet=False, exchange=exchange, limit=2000)
            if not ohlcv:
                logger_main.warning(f"No historical data for {symbol}, skipping market analysis")
                continue
            logger_main.info(f"Successfully fetched {len(ohlcv)} OHLCV data points for {symbol}")

            # Load data into market analysis tools
            market_analyzer.load_data(ohlcv)
            market_rentgen.load_data(ohlcv)

            # Analyze volatility
            volatility = market_analyzer.calculate_volatility(window=14)
            if volatility is None:
                logger_main.warning(f"Failed to calculate volatility for {symbol}, skipping")
                continue
            if volatility < dynamic_thresholds['min_volatility']:
                logger_main.warning(f"Volatility for {symbol} ({volatility:.2%}) is below dynamic threshold ({dynamic_thresholds['min_volatility']:.2%}), skipping")
                continue

            # Detect trend
            trend = market_analyzer.detect_trend(window=20)
            if trend is None:
                logger_main.warning(f"Failed to detect trend for {symbol}, skipping")
                continue
            # Allow all trends for flexibility (dynamic adjustment could be added later)

            # Analyze volume spikes
            volume_spike = market_rentgen.analyze_volume_spikes(threshold=dynamic_thresholds['volume_spike_threshold'])
            if volume_spike is None:
                logger_main.warning(f"Failed to analyze volume spikes for {symbol}, skipping")
                continue
            # Optional: allow symbols without spikes if data is scarce
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

        except Exception as e:
            logger_main.error(f"Error processing symbol {symbol} for user {user_id}: {e}\n{traceback.format_exc()}")
            logger_main.error(f"Backtest results content for debugging: {backtest_results.get(symbol)}")
            continue  # Продолжаем цикл, даже если произошла ошибка
        finally:
            logger_main.debug(f"Finished processing symbol {idx}/{len(symbols)}: {symbol}")
    logger_main.info(f"Completed symbol filtering, found {len(valid_symbols)} valid symbols")
    # Ensure minimum number of symbols (e.g., 10) for trading
    if len(valid_symbols) < 10 and valid_symbols:
        logger_main.warning(f"Only {len(valid_symbols)} symbols found, including top performers to reach minimum of 10")
        valid_symbols = valid_symbols[:10]  # Take top 10 if available
    elif not valid_symbols:
        logger_main.warning("No symbols passed filters, using top 10 by profit from backtest")
        valid_symbols = sorted([(s, backtest_results[s]['profit']) for s in backtest_results if backtest_results[s] and 'profit' in backtest_results[s]], key=lambda x: x[1], reverse=True)[:10]
        valid_symbols = [s for s, _ in valid_symbols]
    return valid_symbols

async def run_trading_for_user(user, exchange_id, model_path, backtest_days, exchange_pool, symbols, backtest_results, dynamic_thresholds):
    """Runs trading for a single user using pre-computed backtest results."""
    logger_main.info(f"Entering run_trading_for_user for user {user['user_id']} on {exchange_id}")
    try:
        user_id = user['user_id']
        testnet = user['testnet']
        logger_main.info(f"Starting trading for user {user_id} on {exchange_id}")

        # Get exchange instance from pool
        logger_main.info(f"Fetching exchange instance for {exchange_id}:{user_id} (testnet: {testnet})")
        exchange = await exchange_pool.get_exchange(exchange_id, user_id, testnet)
        if not exchange:
            logger_main.error(f"Failed to get exchange instance for user {user_id} on {exchange_id}")
            return

        # Debug symbols and backtest_results before processing
        logger_main.debug(f"Symbols type: {type(symbols)}, length: {len(symbols)}")
        logger_main.debug(f"First few symbols: {symbols[:5]}")
        logger_main.debug(f"Backtest results type: {type(backtest_results)}, length: {len(backtest_results)}")
        logger_main.debug(f"Backtest results keys: {list(backtest_results.keys())[:5]}...")

        logger_main.info(f"Using {len(symbols)} pre-filtered symbols for user {user_id}: {symbols[:5]}...")
        logger_main.debug(f"Backtest results keys: {list(backtest_results.keys())[:5]}...")

        # Filter symbols based on backtest results and market analysis
        logger_main.info(f"Calling filter_symbols for user {user_id}")
        try:
            valid_symbols = await filter_symbols(symbols, backtest_results, user_id, exchange_pool, exchange_id, dynamic_thresholds)
        except Exception as e:
            logger_main.error(f"Error in filter_symbols for user {user_id}: {e}\n{traceback.format_exc()}")
            raise  # Перебрасываем исключение, чтобы увидеть полный стек вызовов
        logger_main.info(f"filter_symbols returned {len(valid_symbols)} valid symbols for user {user_id}")

        if not valid_symbols:
            logger_main.error(f"No symbols passed filters for user {user_id}, stopping")
            return

        logger_main.info(f"Starting trading with {len(valid_symbols)} symbols for user {user_id}: {valid_symbols[:5]}...")

        # Start trading
        logger_main.debug(f"Creating trade_task for user {user_id}")
        trade_task = asyncio.create_task(start_trading_all(
            exchange_id, user_id, valid_symbols,
            leverage=1.0,
            order_type='limit',
            trade_percentage=0.1,
            rsi_overbought=70,
            rsi_oversold=30,
            margin_multiplier=2.0,
            blacklisted_symbols=['BTCUSDT'],  # Example blacklist
            model_path=model_path,
            test_mode=testnet
        ))

        # Schedule trade pool cleanup
        logger_main.debug(f"Creating cleanup_task for user {user_id}")
        cleanup_task = asyncio.create_task(schedule_trade_pool_cleanup(
            exchange_id, user_id, max_age_seconds=86400, interval=3600
        ))

        # Monitor positions
        logger_main.debug(f"Creating monitor_task for user {user_id}")
        monitor_task = asyncio.create_task(monitor_positions(
            exchange_id, user_id, exchange, testnet=testnet
        ))

        # Schedule model retraining in the background
        logger_main.debug(f"Creating retrain_task for user {user_id}")
        retraining_manager = RetrainingManager(retrain_interval=86400)
        async def data_loader():
            # Load data for retraining
            from ml_data_preparer import prepare_ml_data
            from historical_data_fetcher import fetch_historical_data
            from data_collector import collect_training_data
            # Получить данные из пула сделок
            trade_data = await collect_training_data(exchange_id, user_id, testnet=testnet)
            # Получить исторические данные
            if not valid_symbols:
                logger_main.error(f"No valid symbols available for retraining for user {user_id}")
                return None, None, None, None
            # Используем BTCUSDT для переобучения и увеличиваем временной диапазон до 90 дней
            retrain_symbol = "BTCUSDT"
            logger_main.info(f"Fetching historical data for retraining using symbol {retrain_symbol}")
            data = await fetch_historical_data(exchange_id, user_id, retrain_symbol, since=int(time.time()) - 90*24*60*60, testnet=testnet, exchange=exchange)
            if data is None:
                logger_main.error(f"Failed to fetch historical data for retraining for user {user_id}")
                return None, None, None, None
            # Преобразуем данные в pandas DataFrame
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            # Подготовить данные для обучения
            result = prepare_ml_data(df, trade_data)
            if len(result) == 2:
                X, y = result
                return X, y, None, None
            elif len(result) == 3:
                X, y, _ = result
                return X, y, None, None
            else:
                logger_main.error(f"Unexpected return value from prepare_ml_data: {result}")
                return None, None, None, None

        from ml_model_trainer import train_model
        # Запускаем переобучение в фоновом режиме
        retrain_task = asyncio.create_task(retraining_manager.schedule_retraining(
            data_loader, train_model, model_path
        ))

        # Wait for trading, cleanup, and monitoring tasks to complete
        logger_main.info(f"Starting tasks for user {user_id}: trade, cleanup, monitor")
        try:
            await asyncio.gather(trade_task, cleanup_task, monitor_task, return_exceptions=True)
        except Exception as e:
            logger_main.error(f"Error in asyncio.gather for user {user_id}: {e}\n{traceback.format_exc()}")
            raise  # Перебрасываем исключение, чтобы asyncio.gather его поймал

        # Stop retraining task
        retraining_manager.stop()
        await retrain_task  # Ждём завершения переобучения
        logger_main.info(f"All tasks completed for user {user_id}")

    except Exception as e:
        logger_main.error(f"Error in run_trading_for_user for user {user_id} on {exchange_id}: {e}\n{traceback.format_exc()}")
        raise  # Перебрасываем исключение, чтобы asyncio.gather его поймал

if __name__ == "__main__":
    print("Starting asyncio.run(main())")
    asyncio.run(main())
    print("Finished asyncio.run(main())")
