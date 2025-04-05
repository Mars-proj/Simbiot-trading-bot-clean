import asyncio
import json
import os
from logging_setup import logger_main
from start_trading_all import start_trading_all, run_backtest
from bot_user_data import BotUserData
from test_symbols import get_test_symbols
from exchange_pool import ExchangePool
from market_state_analyzer import analyze_market_state, calculate_dynamic_thresholds
from symbol_filter import filter_symbols
from trading_manager import run_trading_for_user
import traceback

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
            from backtest_manager import run_backtests
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

        # Analyze market state and calculate dynamic thresholds
        market_state = await analyze_market_state(exchange_pool, exchange_id)
        dynamic_thresholds = await calculate_dynamic_thresholds(exchange_pool, exchange_id, backtest_results, market_state)

        # Process each user with the backtest results
        logger_main.info("Processing users with backtest results")
        tasks = []
        for user in users:
            logger_main.info(f"Starting processing for user {user['user_id']}")
            try:
                task = asyncio.create_task(run_trading_for_user(
                    user, exchange_id, model_path, backtest_days, exchange_pool, symbols, backtest_results, dynamic_thresholds, market_state
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

if __name__ == "__main__":
    print("Starting asyncio.run(main())")
    asyncio.run(main())
    print("Finished asyncio.run(main())")
