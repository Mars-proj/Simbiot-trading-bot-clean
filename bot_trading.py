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
from deposit_calculator import calculate_deposit
from signal_blacklist import SignalBlacklist

async def run_trading_bot(exchange_id, user_id, symbol, leverage=1.0, order_type='limit', trade_percentage=0.1, rsi_overbought=70, rsi_oversold=30, margin_multiplier=2.0, blacklisted_symbols=None, model_path=None, test_mode=False):
    """Runs the trading bot for a specific symbol with configurable parameters."""
    try:
        # Validate inputs
        if not user_data.get_user_status(user_id):
            logger_main.error(f"User {user_id} not found or inactive")
            return False
        if not user_data.has_api_keys(user_id, exchange_id):
            logger_main.error(f"User {user_id} does not have API keys for {exchange_id}")
            return False
        if not await validate_symbol(exchange_id, user_id, symbol, testnet=test_mode):
            return False

        # Check if symbol is blacklisted
        blacklist = SignalBlacklist(blacklisted_symbols)
        if blacklist.is_blacklisted(symbol):
            logger_main.error(f"Symbol {symbol} is blacklisted for user {user_id} on {exchange_id}")
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

        # Calculate required deposit
        required_deposit = calculate_deposit(symbol, amount, margin_multiplier)
        if required_deposit is None:
            logger_main.error(f"Failed to calculate required deposit for {symbol}")
            return False

        # Check if available balance is sufficient for the deposit
        if available_balance < required_deposit:
            logger_main.error(f"Insufficient balance for user {user_id} on {exchange_id}: available={available_balance}, required={required_deposit}")
            return False

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
        signal = await process_signals(exchange_id, user_id, symbol, model_path=model_path, rsi_overbought=rsi_overbought, rsi_oversold=rsi_oversold)
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
