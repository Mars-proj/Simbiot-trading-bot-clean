import asyncio
from logging_setup import logger_main
from start_trading_all import start_trading_all
from trade_pool_manager import schedule_trade_pool_cleanup
from position_monitor import monitor_positions
from retraining_manager import RetrainingManager
from historical_data_fetcher import fetch_historical_data
import pandas as pd

async def run_trading_for_user(user, exchange_id, model_path, backtest_days, exchange_pool, symbols, backtest_results, dynamic_thresholds, market_state):
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

        # Filter symbols based on backtest results and market analysis
        logger_main.info(f"Calling filter_symbols for user {user_id}")
        from symbol_filter import filter_symbols
        try:
            valid_symbols = await filter_symbols(symbols, backtest_results, user_id, exchange_pool, exchange_id, dynamic_thresholds, market_state)
        except Exception as e:
            logger_main.error(f"Error in filter_symbols for user {user_id}: {e}")
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
            from data_collector import collect_training_data
            # Получить данные из пула сделок
            trade_data = await collect_training_data(exchange_id, user_id, testnet=testnet)
            # Получить исторические данные
            if not valid_symbols:
                logger_main.error(f"No valid symbols available for retraining for user {user_id}")
                return None, None, None, None
            # Используем первый доступный символ из valid_symbols для переобучения
            retrain_symbol = valid_symbols[0]
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
            logger_main.error(f"Error in asyncio.gather for user {user_id}: {e}")
            raise  # Перебрасываем исключение, чтобы asyncio.gather его поймал

        # Stop retraining task
        retraining_manager.stop()
        await retrain_task  # Ждём завершения переобучения
        logger_main.info(f"All tasks completed for user {user_id}")

    except Exception as e:
        logger_main.error(f"Error in run_trading_for_user for user {user_id} on {exchange_id}: {e}")
        raise  # Перебрасываем исключение, чтобы asyncio.gather его поймал
