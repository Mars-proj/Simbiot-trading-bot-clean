import asyncio
from logging_setup import logger_main
from trade_executor_core import execute_trade
from trade_executor_signals import process_signals
from bot_user_data import user_data
from symbol_handler import validate_symbol
from limits import check_limits
from balance_manager import BalanceManager
from exchange_factory import create_exchange
from trade_pool_core import TradePool

async def run_trading_bot(exchange_id, user_id, symbol, leverage=1.0, order_type='limit', trade_percentage=0.1, rsi_overbought=70, rsi_oversold=30, test_mode=False):
    """Runs the trading bot for a specific symbol with configurable parameters."""
    try:
        # Validate inputs
        if user_id not in user_data:
            logger_main.error(f"User {user_id} not found in user_data")
            return False
        if not validate_symbol(symbol):
            return False

        # Create exchange instance
        exchange = create_exchange(exchange_id, user_id, testnet=test_mode)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return False

        # Fetch balance
        balance_manager = BalanceManager(user_id)
        balance = await balance_manager.get_balance(exchange)
        if not balance:
            logger_main.error(f"Failed to fetch balance for user {user_id} on {exchange_id}")
            return False

        # Determine currency and calculate amount
        currency = symbol.split('/')[1]  # e.g., USDT in BTC/USDT
        available_balance = balance.get(currency, {}).get('free', 0)
        amount = available_balance * trade_percentage  # Use configurable percentage of available balance

        # Fetch open trades
        trade_pool = TradePool(user_id, exchange_id)
        open_trades = await trade_pool.get_trades(exchange)
        if open_trades is None:
            logger_main.error(f"Failed to fetch open trades for user {user_id} on {exchange_id}")
            return False

        if not check_limits(amount, leverage, open_trades):
            logger_main.error(f"Trade limits exceeded for user {user_id} on {exchange_id}")
            return False

        # Get signal from trade_executor_signals
        signal = await process_signals(exchange_id, user_id, symbol, rsi_overbought=rsi_overbought, rsi_oversold=rsi_oversold)
        if not signal:
            logger_main.error(f"Failed to process signal for {symbol} on {exchange_id}")
            return False

        # Execute trade
        if test_mode:
            logger_main.info(f"[Test Mode] Would execute {order_type} {signal} trade for user {user_id} on {exchange_id}: symbol={symbol}, amount={amount}")
            return True

        order = await execute_trade(exchange_id, user_id, symbol, signal, amount, leverage, order_type, test_mode)
        if not order:
            logger_main.error(f"Failed to execute trade for {symbol} on {exchange_id}")
            return False

        # Log trade details
        logger_main.info(f"Trading bot executed {order_type} {signal} trade for user {user_id} on {exchange_id}: symbol={symbol}, amount={amount}, price={order.get('price', 'N/A')}")
        return True
    except Exception as e:
        logger_main.error(f"Error running trading bot for {symbol} on {exchange_id}: {e}")
        return False
    finally:
        await exchange.close()

__all__ = ['run_trading_bot']
