import asyncio
from logging_setup import logger_main
from bot_trading import run_trading_bot
from bot_user_data import user_data
from exchange_factory import create_exchange
from config_keys import SUPPORTED_EXCHANGES
from signal_blacklist import SignalBlacklist

async def start_trading_all(exchange_id, user_id, symbols, leverage=1.0, order_type='limit', trade_percentage=0.1, rsi_overbought=70, rsi_oversold=30, margin_multiplier=2.0, blacklisted_symbols=None, model_path=None, test_mode=False):
    """Starts trading for all symbols in parallel."""
    try:
        if exchange_id not in SUPPORTED_EXCHANGES:
            logger_main.error(f"Exchange {exchange_id} not supported")
            return False

        # Check user status and API keys
        if not await user_data.get_user_status(user_id):
            logger_main.error(f"User {user_id} is not active")
            return False
        if not await user_data.has_api_keys(user_id, exchange_id):
            logger_main.error(f"No API keys found for user {user_id} on {exchange_id}")
            return False

        # Create exchange instance
        exchange = create_exchange(exchange_id, user_id, testnet=test_mode)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return False

        # Initialize signal blacklist
        blacklist = SignalBlacklist(blacklisted_symbols or [])

        # Start trading tasks for each symbol
        tasks = []
        for symbol in symbols:
            if blacklist.is_blacklisted(symbol):
                logger_main.info(f"Symbol {symbol} is blacklisted, skipping")
                continue

            task = asyncio.create_task(run_trading_bot(
                exchange_id, user_id, symbol,
                leverage=leverage,
                order_type=order_type,
                trade_percentage=trade_percentage,
                rsi_overbought=rsi_overbought,
                rsi_oversold=rsi_oversold,
                margin_multiplier=margin_multiplier,
                model_path=model_path,
                test_mode=test_mode
            ))
            tasks.append(task)

        # Wait for all trading tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger_main.error(f"Trading failed for {symbol} on {exchange_id} (live): {result}")
            else:
                logger_main.info(f"Trading result for {symbol} on {exchange_id} (live): {result}")

        return True
    except Exception as e:
        logger_main.error(f"Error starting trading for all symbols on {exchange_id}: {e}")
        return False
    finally:
        if 'exchange' in locals():
            logger_main.info(f"Closing exchange connection in start_trading_all for {exchange_id}")
            await exchange.close()

__all__ = ['start_trading_all']
