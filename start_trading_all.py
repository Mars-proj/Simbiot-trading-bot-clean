import asyncio
from logging_setup import logger_main
from bot_trading import run_trading_bot
from bot_user_data import user_data
from config_keys import SUPPORTED_EXCHANGES
from symbol_handler import validate_symbol
from limits import check_limits
from trade_pool_core import TradePool
from exchange_factory import create_exchange
from balance_manager import BalanceManager
from deposit_calculator import calculate_deposit
from signal_blacklist import SignalBlacklist

async def start_trading_all(exchange_id, user_id, symbols, leverage=1.0, order_type='limit', trade_percentage=0.1, rsi_overbought=70, rsi_oversold=30, margin_multiplier=2.0, blacklisted_symbols=None, model_path=None, test_mode=False):
    """Starts trading for all symbols in parallel with configurable parameters."""
    try:
        # Validate inputs
        if exchange_id not in SUPPORTED_EXCHANGES:
            logger_main.error(f"Exchange {exchange_id} not supported")
            return False
        if not user_data.get_user_status(user_id):
            logger_main.error(f"User {user_id} not found or inactive")
            return False
        if not user_data.has_api_keys(user_id, exchange_id):
            logger_main.error(f"User {user_id} does not have API keys for {exchange_id}")
            return False
        if not isinstance(symbols, list):
            logger_main.error(f"Symbols must be a list, got {type(symbols)}")
            return False
        for symbol in symbols:
            if not await validate_symbol(exchange_id, user_id, symbol, testnet=test_mode):
                return False

        # Check if any symbol is blacklisted
        blacklist = SignalBlacklist(blacklisted_symbols)
        filtered_symbols = [symbol for symbol in symbols if not blacklist.is_blacklisted(symbol)]
        if not filtered_symbols:
            logger_main.error(f"All symbols are blacklisted for user {user_id} on {exchange_id}")
            return False
        if len(filtered_symbols) < len(symbols):
            logger_main.warning(f"Some symbols were blacklisted: {set(symbols) - set(filtered_symbols)}")

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

        # Fetch open trades
        trade_pool = TradePool(user_id, exchange_id)
        open_trades = await trade_pool.get_trades(exchange)
        if open_trades is None:
            logger_main.error(f"Failed to fetch open trades for user {user_id} on {exchange_id}")
            return False

        # Run trading for all symbols in parallel
        tasks = []
        for symbol in filtered_symbols:
            # Determine currency and calculate amount for each symbol
            currency = symbol.split('/')[1]  # e.g., USDT in BTC/USDT
            available_balance = balance.get(currency, {}).get('free', 0)
            amount = available_balance * trade_percentage  # Use configurable percentage of available balance

            # Calculate required deposit
            required_deposit = calculate_deposit(symbol, amount, margin_multiplier)
            if required_deposit is None:
                logger_main.error(f"Failed to calculate required deposit for {symbol}")
                continue

            # Check if available balance is sufficient for the deposit
            if available_balance < required_deposit:
                logger_main.error(f"Insufficient balance for user {user_id} on {exchange_id} for {symbol}: available={available_balance}, required={required_deposit}")
                continue

            if not check_limits(amount, leverage, open_trades):
                logger_main.error(f"Trade limits exceeded for user {user_id} on {exchange_id} for symbol {symbol}")
                continue

            tasks.append(run_trading_bot(
                exchange_id, user_id, symbol,
                leverage=leverage,
                order_type=order_type,
                trade_percentage=trade_percentage,
                rsi_overbought=rsi_overbought,
                rsi_oversold=rsi_oversold,
                margin_multiplier=margin_multiplier,
                blacklisted_symbols=blacklisted_symbols,
                model_path=model_path,
                test_mode=test_mode
            ))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log results for each symbol
        for symbol, result in zip(filtered_symbols, results):
            if isinstance(result, Exception):
                logger_main.error(f"Failed trading for {symbol} on {exchange_id}: {result}")
            else:
                status = "success" if result else "failed"
                logger_main.info(f"Trading result for {symbol} on {exchange_id} ({'test mode' if test_mode else 'live'}): {status}")

        successful = sum(1 for r in results if r is True)
        logger_main.info(f"Completed trading for {successful}/{len(filtered_symbols)} symbols for user {user_id} on {exchange_id} ({'test mode' if test_mode else 'live'})")
        return successful > 0
    except Exception as e:
        logger_main.error(f"Error starting trading for user {user_id} on {exchange_id}: {e}")
        return False
    finally:
        await exchange.close()

__all__ = ['start_trading_all']
