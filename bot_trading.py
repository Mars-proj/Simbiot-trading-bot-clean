import asyncio
from logging_setup import logger_main
from trade_executor_core import execute_trade
from trade_executor_signals import process_signals
from bot_user_data import user_data
from symbol_handler import validate_symbol
from limits import check_limits

async def run_trading_bot(exchange_id, user_id, symbol):
    """Runs the trading bot for a specific symbol."""
    try:
        # Validate inputs
        if user_id not in user_data:
            logger_main.error(f"User {user_id} not found in user_data")
            return False
        if not validate_symbol(symbol):
            return False

        # Fetch open trades (placeholder)
        open_trades = []  # This should be fetched from trade_pool_core
        amount = 0.1  # Placeholder
        leverage = 1  # Placeholder
        if not check_limits(amount, leverage, open_trades):
            logger_main.error(f"Trade limits exceeded for user {user_id} on {exchange_id}")
            return False

        # Get signal from trade_executor_signals
        signal = await process_signals(exchange_id, user_id, symbol)
        if not signal:
            logger_main.error(f"Failed to process signal for {symbol} on {exchange_id}")
            return False

        # Execute trade
        order = await execute_trade(exchange_id, user_id, symbol, signal)
        if not order:
            logger_main.error(f"Failed to execute trade for {symbol} on {exchange_id}")
            return False

        # Log trade details
        logger_main.info(f"Trading bot executed trade for user {user_id} on {exchange_id}: symbol={symbol}, signal={signal}, amount={amount}, price={order.get('price', 'N/A')}")
        return True
    except Exception as e:
        logger_main.error(f"Error running trading bot for {symbol} on {exchange_id}: {e}")
        return False

__all__ = ['run_trading_bot']
