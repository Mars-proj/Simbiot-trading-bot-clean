import asyncio
from logging_setup import logger_main
from start_trading_all import start_trading_all
from bot_user_data import user_data
from test_symbols import get_test_symbols
from trade_pool_manager import schedule_trade_pool_cleanup
from position_monitor import monitor_positions
from retraining_manager import RetrainingManager
from backtest_cycle import run_backtest
import time

async def main():
    """Main entry point for the trading bot system."""
    try:
        # Configuration
        exchange_id = "mexc"  # Use MEXC for real trading
        user_id = "user1"  # Use user1
        testnet = False  # Use real trading mode
        model_path = "models/trading_model.pth"  # Example model path
        backtest_days = 30  # Number of days for backtest
        min_profit_threshold = 0.05  # Minimum profit threshold for backtest (5%)

        # Fetch test symbols
        logger_main.info("Fetching test symbols")
        symbols = await get_test_symbols(exchange_id, user_id, testnet=testnet)
        if not symbols:
            logger_main.error("No valid symbols found for trading, stopping")
            return

        logger_main.info(f"Selected symbols for backtesting: {symbols[:5]}...")

        # Run backtest for each symbol
        valid_symbols = []
        for symbol in symbols:
            logger_main.info(f"Running backtest for {symbol} on {exchange_id}")
            backtest_result = await run_backtest(
                exchange_id, user_id, symbol,
                days=backtest_days,
                leverage=1.0,
                trade_percentage=0.1,
                rsi_overbought=70,
                rsi_oversold=30,
                test_mode=testnet
            )
            if backtest_result is None:
                logger_main.warning(f"Backtest failed for {symbol}, skipping")
                continue

            profit = backtest_result.get('profit', 0)
            if profit < min_profit_threshold:
                logger_main.warning(f"Backtest profit for {symbol} ({profit:.2%}) is below threshold ({min_profit_threshold:.2%}), skipping")
                continue

            valid_symbols.append(symbol)
            logger_main.info(f"Backtest successful for {symbol}: profit={profit:.2%}")

        if not valid_symbols:
            logger_main.error("No symbols passed backtest, stopping")
            return

        logger_main.info(f"Starting trading with symbols: {valid_symbols[:5]}...")

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
            # Load data for retraining (example implementation)
            from ml_data_preparer import prepare_ml_data
            from historical_data_fetcher import fetch_historical_data
            # Use the first valid symbol for retraining
            if not valid_symbols:
                logger_main.error("No valid symbols available for retraining")
                return None, None, None, None
            data = await fetch_historical_data(exchange_id, user_id, valid_symbols[0], since=int(time.time()) - 30*24*60*60, testnet=testnet)
            if data is None:
                logger_main.error("Failed to fetch historical data for retraining")
                return None, None, None, None
            return prepare_ml_data(data)

        from ml_model_trainer import train_model
        retrain_task = asyncio.create_task(retraining_manager.schedule_retraining(
            data_loader, train_model, model_path
        ))

        # Wait for tasks to complete
        await asyncio.gather(trade_task, cleanup_task, monitor_task, retrain_task)
    except Exception as e:
        logger_main.error(f"Error in main loop: {e}")

if __name__ == "__main__":
    asyncio.run(main())
