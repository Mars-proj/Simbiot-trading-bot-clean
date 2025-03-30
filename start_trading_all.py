import asyncio
from logging_setup import logger_main
from bot_trading import run_trading_bot
from bot_user_data import user_data
from config_keys import SUPPORTED_EXCHANGES
from symbol_handler import validate_symbol
from limits import check_limits

async def start_trading_all(exchange_id, user_id, symbols):
    """Starts trading for all symbols in parallel."""
    try:
        # Validate inputs
        if exchange_id not in SUPPORTED_EXCHANGES:
            logger_main.error(f"Exchange {exchange_id} not supported")
            return False
        if user_id not in user_data:
            logger_main.error(f"User {user_id} not found in user_data")
            return False
        if not isinstance(symbols, list):
            logger_main.error(f"Symbols must be a list, got {type(symbols)}")
            return False
        for symbol in symbols:
            if not validate_symbol(symbol):
                return False

        # Fetch open trades (placeholder)
        open_trades = []  # This should be fetched from trade_pool_core
        amount = 0.1  # Placeholder per symbol
        leverage = 1  # Placeholder
        if not check_limits(amount * len(symbols), leverage, open_trades):
            logger_main.error(f"Trade limits exceeded for user {user_id} on {exchange_id}")
            return False

        # Run trading for all symbols in parallel
        tasks = [run_trading_bot(exchange_id, user_id, symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log results for each symbol
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger_main.error(f"Failed trading for {symbol} on {exchange_id}: {result}")
            else:
                status = "success" if result else "failed"
                logger_main.info(f"Trading result for {symbol} on {exchange_id}: {status}")

        successful = sum(1 for r in results if r is True)
        logger_main.info(f"Completed trading for {successful}/{len(symbols)} symbols for user {user_id} on {exchange_id}")
        return successful > 0
    except Exception as e:
        logger_main.error(f"Error starting trading for user {user_id} on {exchange_id}: {e}")
        return False

__all__ = ['start_trading_all']
