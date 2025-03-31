from logging_setup import logger_main
from config_keys import API_KEYS, validate_api_keys
from symbol_handler import validate_symbol
from exchange_factory import create_exchange
from balance_manager import BalanceManager

async def manage_deposit(exchange_id, user_id, symbol, amount):
    """Manages deposits for a user on a specific exchange."""
    try:
        # Validate API keys
        if user_id not in API_KEYS or exchange_id not in API_KEYS[user_id]:
            logger_main.error(f"No API keys found for user {user_id} on {exchange_id}")
            return False
        api_key = API_KEYS[user_id][exchange_id]["api_key"]
        api_secret = API_KEYS[user_id][exchange_id]["api_secret"]
        if not validate_api_keys(api_key, api_secret):
            logger_main.error(f"Invalid API keys for user {user_id} on {exchange_id}")
            return False

        # Validate symbol
        if not validate_symbol(symbol):
            logger_main.error(f"Invalid symbol: {symbol}")
            return False

        # Create exchange instance
        exchange = create_exchange(exchange_id, user_id, testnet=False)
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

        # Check if sufficient balance for deposit
        if available_balance < amount:
            logger_main.error(f"Insufficient balance for deposit: available={available_balance}, required={amount}")
            return False

        # Placeholder: Call exchange API to manage deposit (e.g., transfer to trading account)
        logger_main.info(f"Managed deposit for user {user_id} on {exchange_id}: symbol={symbol}, amount={amount}, currency={currency}")
        return True
    except Exception as e:
        logger_main.error(f"Error managing deposit for user {user_id} on {exchange_id}: {e}")
        return False
    finally:
        await exchange.close()

__all__ = ['manage_deposit']
