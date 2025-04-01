import asyncio
from logging_setup import logger_main
from start_trading_all import start_trading_all
from bot_user_data import user_data
from test_symbols import get_test_symbols
from trade_pool_manager import schedule_trade_pool_cleanup
from position_monitor import monitor_positions
from retraining_manager import RetrainingManager

async def main():
    """Main entry point for the trading bot system."""
    try:
        # Configuration
        exchange_id = "binance"  # Example exchange
        user_id = "user123"  # Example user
        testnet = True  # Use testnet for safety
        model_path = "models/trading_model.pth"  # Example model path

        # Add user with API keys (example)
        api_keys = {
            exchange_id: {
                "api_key": "your_api_key",
                "api_secret": "your_api_secret"
            }
        }
        await user_data.add_user(user_id, api_keys=api_keys)

        # Fetch test symbols
        symbols = await get_test_symbols(exchange_id, user_id, testnet=testnet)
        if not symbols:
            logger_main.error("No valid symbols found for trading")
            return

        # Start trading
        trade_task = asyncio.create_task(start_trading_all(
            exchange_id, user_id, symbols,
            leverage=1.0,
            order_type='limit',
            trade_percentage=0.1,
            rsi_overbought=70,
            rsi_oversold=30,
            margin_multiplier=2.0,
            blacklisted_symbols=['BTC/USDT'],  # Example blacklist
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

        # Schedule model retraining (example data loader and trainer)
        retraining_manager = RetrainingManager(retrain_interval=86400)
        async def dummy_data_loader():
            # Placeholder: Replace with actual data loading logic
            import numpy as np
            X = np.random.rand(1000, 5)
            y = np.random.randint(0, 2, 1000)
            return X[:800], y[:800], X[800:], y[800:]

        from ml_model_trainer import train_model
        retrain_task = asyncio.create_task(retraining_manager.schedule_retraining(
            dummy_data_loader, train_model, model_path
        ))

        # Wait for tasks to complete
        await asyncio.gather(trade_task, cleanup_task, monitor_task, retrain_task)
    except Exception as e:
        logger_main.error(f"Error in main loop: {e}")

if __name__ == "__main__":
    asyncio.run(main())
