import asyncio
import json
import os
from logging_setup import logger_main
from start_trading_all import start_trading_all, run_backtest
from bot_user_data import BotUserData
from test_symbols import get_test_symbols
from trade_pool_manager import schedule_trade_pool_cleanup
from position_monitor import monitor_positions
from retraining_manager import RetrainingManager
from exchange_pool import ExchangePool
from cache_utils import CacheUtils
import time
import traceback

async def main():
    """Main entry point for the trading bot system."""
    try:
        # Configuration
        exchange_id = "mexc"  # Use MEXC for real trading
        users = [
            {"user_id": "user1", "testnet": False},
            {"user_id": "user2", "testnet": False},
            # Add more users for scalability testing
        ]
        model_path = "models/trading_model.pth"  # Example model path
        backtest_days = 7  # Reduced number of days for backtest (was 30)
        min_profit_threshold = 0.01  # Reduced threshold (was 0.05)

        # Process all users asynchronously
        await process_users(users, exchange_id, model_path, backtest_days, min_profit_threshold)

    except Exception as e:
        logger_main.error(f"Error in main loop: {e}\n{traceback.format_exc()}")

async def process_users(users, exchange_id, model_path, backtest_days, min_profit_threshold):
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
            symbols = await get_test_symbols(exchange_id, user_id, testnet=testnet)
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

        # Process each user with the backtest results
        logger_main.info("Processing users with backtest results")
        tasks = []
        for user in users:
            logger_main.info(f"Starting processing for user {user['user_id']}")
            task = asyncio.create_task(run_trading_for_user(
                user, exchange_id, model_path, backtest_days, min_profit_threshold, exchange_pool, symbols, backtest_results
            ))
            tasks.append(task)
        logger_main.info(f"Created {len(tasks)} tasks for processing users")

        # Wait for all tasks to complete and handle exceptions
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for idx, (user, result) in enumerate(zip(users, results)):
            if isinstance(result, Exception):
                logger_main.error(f"Task {idx} for user {user['user_id']} failed with exception: {result}\n{traceback.format_exc()}")
            else:
                logger_main.info(f"Task {idx} for user {user['user_id']} completed successfully with result: {result}")
    except Exception as e:
        logger_main.error(f"Error in process_users: {e}\n{traceback.format_exc()}")
    finally:
        logger_main.info("Closing all exchange instances in ExchangePool")
        await exchange_pool.close_all()

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

async def filter_symbols(symbols, backtest_results, user_id, min_profit_threshold):
    """Filters symbols based on backtest results."""
    valid_symbols = []
    logger_main.info(f"Starting symbol filtering for {len(symbols)} symbols")
    for idx, symbol in enumerate(symbols):
        logger_main.debug(f"Processing symbol {idx}/{len(symbols)}: {symbol}, type: {type(symbol)}")
        try:
            # Additional debug logging
            logger_main.debug(f"Attempting to access backtest_results for symbol: {symbol}")
            result = backtest_results.get(symbol)
            logger_main.debug(f"Backtest result for {symbol}: {result}")
            if result is None:
                logger_main.warning(f"No backtest result for {symbol} for user {user_id}, skipping")
                continue
            # Additional debug logging
            logger_main.debug(f"Attempting to access 'profit' in result: {result}")
            profit = result.get('profit', 0)
            logger_main.debug(f"Backtest profit for {symbol}: {profit:.2%}, threshold: {min_profit_threshold:.2%}")
            if profit < min_profit_threshold:
                logger_main.warning(f"Backtest profit for {symbol} ({profit:.2%}) is below threshold ({min_profit_threshold:.2%}) for user {user_id}, skipping")
                continue
            valid_symbols.append(symbol)
            logger_main.info(f"Backtest successful for {symbol} for user {user_id}: profit={profit:.2%}")
        except Exception as e:
            logger_main.error(f"Error processing symbol {symbol} for user {user_id}: {e}\n{traceback.format_exc()}")
            continue
    return valid_symbols

async def run_trading_for_user(user, exchange_id, model_path, backtest_days, min_profit_threshold, exchange_pool, symbols, backtest_results):
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

        # Filter symbols based on backtest results
        valid_symbols = await filter_symbols(symbols, backtest_results, user_id, min_profit_threshold)

        if not valid_symbols:
            logger_main.error(f"No symbols passed backtest for user {user_id}, stopping")
            return

        logger_main.info(f"Starting trading with {len(valid_symbols)} symbols for user {user_id}: {valid_symbols[:5]}...")

        # Start trading
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
        cleanup_task = asyncio.create_task(schedule_trade_pool_cleanup(
            exchange_id, user_id, max_age_seconds=86400, interval=3600
        ))

        # Monitor positions
        monitor_task = asyncio.create_task(monitor_positions(
            exchange_id, user_id, testnet=testnet
        ))

        # Schedule model retraining
        retraining_manager = RetrainingManager(retrain_interval=86400)
        async def data_loader():
            # Load data for retraining
            from ml_data_preparer import prepare_ml_data
            from historical_data_fetcher import fetch_historical_data
            from data_collector import collect_training_data
            # Получить данные из пула сделок
            trade_data = await collect_training_data(exchange_id, user_id)
            # Получить исторические данные
            if not valid_symbols:
                logger_main.error(f"No valid symbols available for retraining for user {user_id}")
                return None, None, None, None
            data = await fetch_historical_data(exchange_id, user_id, valid_symbols[0], since=int(time.time()) - 30*24*60*60, testnet=testnet)
            if data is None:
                logger_main.error(f"Failed to fetch historical data for retraining for user {user_id}")
                return None, None, None, None
            # Подготовить данные для обучения
            X, y = prepare_ml_data(data, trade_data)
            return X, y, None, None

        from ml_model_trainer import train_model
        retrain_task = asyncio.create_task(retraining_manager.schedule_retraining(
            data_loader, train_model, model_path
        ))

        # Wait for tasks to complete
        logger_main.info(f"Starting tasks for user {user_id}: trade, cleanup, monitor, retrain")
        await asyncio.gather(trade_task, cleanup_task, monitor_task, retrain_task)
        logger_main.info(f"All tasks completed for user {user_id}")
    except Exception as e:
        logger_main.error(f"Error in run_trading_for_user for user {user_id} on {exchange_id}: {e}\n{traceback.format_exc()}")
        raise  # Перебрасываем исключение, чтобы asyncio.gather его поймал

if __name__ == "__main__":
    asyncio.run(main())
