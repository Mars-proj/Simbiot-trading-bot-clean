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

async def start_trading_all(exchange_id, user_id, symbols, leverage=1.0, order_type='limit', trade_percentage=0.1, rsi_overbought=70, rsi_oversold=30, test_mode=False):
    """Starts trading for all symbols in parallel with configurable parameters."""
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
        for symbol in symbols:
            # Determine currency and calculate amount for each symbol
            currency = symbol.split('/')[1]  # e.g., USDT in BTC/USDT
            available_balance = balance.get(currency, {}).get('free', 0)
            amount = available_balance * trade_percentage  # Use configurable percentage of available balance

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
                test_mode=test_mode
            ))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log results for each symbol
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger_main.error(f"Failed trading for {symbol} on {exchange_id}: {result}")
            else:
                status = "success" if result else "failed"
                logger_main.info(f"Trading result for {symbol} on {exchange_id} ({'test mode' if test_mode else 'live'}): {status}")

        successful = sum(1 for r in results if r is True)
        logger_main.info(f"Completed trading for {successful}/{len(symbols)} symbols for user {user_id} on {exchange_id} ({'test mode' if test_mode else 'live'})")
        return successful > 0
    except Exception as e:
        logger_main.error(f"Error starting trading for user {user_id} on {exchange_id}: {e}")
        return False
    finally:
        await exchange.close()

__all__ = ['start_trading_all']
