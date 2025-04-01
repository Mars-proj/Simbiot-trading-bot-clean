from logging_setup import logger_main
from config_keys import SUPPORTED_EXCHANGES
from exchange_factory import create_exchange
from balance_manager import BalanceManager
from symbol_handler import validate_symbol

async def manage_deposit(exchange_id, user_id, symbol, amount, testnet=False):
    """Manages deposits for a trade on a specific exchange."""
    try:
        if exchange_id not in SUPPORTED_EXCHANGES:
            logger_main.error(f"Exchange {exchange_id} not supported")
            return False
        if amount <= 0:
            logger_main.error(f"Invalid deposit amount: {amount}")
            return False
        if not await validate_symbol(exchange_id, user_id, symbol, testnet=testnet):
            return False

        # Create exchange instance
        exchange = create_exchange(exchange_id, user_id, testnet=testnet)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return False

        # Fetch balance
        balance_manager = BalanceManager(user_id)
        balance = await balance_manager.get_balance(exchange)
        if not balance:
            logger_main.error(f"Failed to fetch balance for user {user_id} on {exchange_id}")
            return False

        # Determine currency
        currency = symbol.split('/')[1]  # e.g., USDT in BTC/USDT
        available_balance = balance.get(currency, {}).get('free', 0)
        total_balance = balance.get(currency, {}).get('total', 0)

        # Check if sufficient balance is available
        if available_balance < amount:
            logger_main.error(f"Insufficient available balance for deposit: available={available_balance}, required={amount}, total={total_balance}, currency={currency}")
            return False

        # In test mode, just log the action
        if testnet:
            logger_main.info(f"[Test Mode] Would manage deposit for user {user_id} on {exchange_id}: symbol={symbol}, amount={amount}, currency={currency}")
            return True

        # In live mode, we assume the deposit is already available (handled by the user)
        logger_main.info(f"Managed deposit for user {user_id} on {exchange_id}: symbol={symbol}, amount={amount}, currency={currency}, available_balance={available_balance}, total_balance={total_balance}")
        return True
    except Exception as e:
        logger_main.error(f"Error managing deposit for user {user_id} on {exchange_id}: {e}")
        return False
    finally:
        await exchange.close()

__all__ = ['manage_deposit']
