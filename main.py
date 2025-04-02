import asyncio
import json
import os
from logging_setup import logger_main
from start_trading_all import start_trading_all
from bot_user_data import BotUserData
from test_symbols import get_test_symbols
from trade_pool_manager import schedule_trade_pool_cleanup
from position_monitor import monitor_positions
from retraining_manager import RetrainingManager
from exchange_pool import ExchangePool
from cache_utils import CacheUtils
import time

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
        backtest_days = 30  # Number of days for backtest
        min_profit_threshold = 0.05  # Minimum profit threshold for backtest (5%)

        # Process all users asynchronously
        await process_users(users, exchange_id, model_path, backtest_days, min_profit_threshold)

    except Exception as e:
        logger_main.error(f"Error in main loop: {e}")

async def process_users(users, exchange_id, model_path, backtest_days, min_profit_threshold):
    """Processes trading for all users asynchronously."""
    exchange_pool = ExchangePool()
    try:
        # Check if selected pairs file exists
        selected_pairs_file = "selected_pairs.json"
        if os.path.exists(selected_pairs_file):
            with open(selected_pairs_file, 'r') as f:
                symbols = json.load(f)
            logger_main.info(f"Loaded {len(symbols)} selected pairs from {selected_pairs_file}: {symbols[:5]}...")
        else:
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

        # Process each user with the selected symbols
        tasks = []
        for user in users:
            logger_main.info(f"Starting processing for user {user['user_id']}")
            tasks.append(asyncio.create_task(run_trading_for_user(
                user, exchange_id, model_path, backtest_days, min_profit_threshold, exchange_pool, symbols
            )))
        await asyncio.gather(*tasks)
    finally:
        await exchange_pool.close_all()

async def run_trading_for_user(user, exchange_id, model_path, backtest_days, min_profit_threshold, exchange_pool, symbols):
    """Runs trading for a single user."""
    try:
        user_id = user['user_id']
        testnet = user['testnet']
        logger_main.info(f"Starting trading for user {user_id} on {exchange_id}")

        # Get exchange instance from pool
        exchange = await exchange_pool.get_exchange(exchange_id, user_id, testnet)
        if not exchange:
            logger_main.error(f"Failed to get exchange instance for user {user_id} on {exchange_id}")
            return

        logger_main.info(f"Using {len(symbols)} pre-filtered symbols for user {user_id}: {symbols[:5]}...")

        # Run backtest for each symbol
        valid_symbols = []
        backtests_completed = 0
        for symbol in symbols:
            logger_main.info(f"Running backtest for {symbol} on {exchange_id} for user {user_id}")
            backtest_result = await run_backtest(
                exchange_id, user_id, symbol,
                days=backtest_days,
                leverage=1.0,
                trade_percentage=0.1,
                rsi_overbought=70,
                rsi_oversold=30,
                test_mode=testnet
            )
            backtests_completed += 1
            logger_main.info(f"Backtest completed for {symbol}. Total backtests completed: {backtests_completed}/{len(symbols)}")
            if backtest_result is None:
                logger_main.warning(f"Backtest failed for {symbol} for user {user_id}, skipping")
                continue

            profit = backtest_result.get('profit', 0)
            logger_main.debug(f"Backtest profit for {symbol}: {profit:.2%}, threshold: {min_profit_threshold:.2%}")
            if profit < min_profit_threshold:
                logger_main.warning(f"Backtest profit for {symbol} ({profit:.2%}) is below threshold ({min_profit_threshold:.2%}) for user {user_id}, skipping")
                continue

            valid_symbols.append(symbol)
            logger_main.info(f"Backtest successful for {symbol} for user {user_id}: profit={profit:.2%}")

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
        await asyncio.gather(trade_task, cleanup_task, monitor_task, retrain_task)
    except Exception as e:
        logger_main.error(f"Error in run_trading_for_user for user {user_id} on {exchange_id}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
