from logging_setup import logger_main
from config_keys import API_KEYS, validate_api_keys
from symbol_handler import validate_symbol
from exchange_factory import create_exchange
from balance_manager import BalanceManager

async def manage_deposit(exchange_id, user_id, symbol, amount, testnet=False):
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
        if not await validate_symbol(exchange_id, user_id, symbol, testnet=testnet):
            logger_main.error(f"Invalid symbol: {symbol}")
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

        # Check if sufficient balance for deposit
        if available_balance < amount:
            logger_main.error(f"Insufficient balance for deposit: available={available_balance}, required={amount}")
            return False

        # Transfer funds to trading account (e.g., futures or margin account)
        if testnet:
            logger_main.info(f"[Test Mode] Would transfer {amount} {currency} to trading account for user {user_id} on {exchange_id}")
        else:
            # Check if exchange supports transfer
            if not hasattr(exchange, 'transfer'):
                logger_main.error(f"Exchange {exchange_id} does not support transfer API")
                return False

            # Perform the transfer (example: to futures account)
            transfer_result = await exchange.transfer(currency, amount, 'main', 'futures')
            if not transfer_result or 'id' not in transfer_result:
                logger_main.error(f"Failed to transfer {amount} {currency} to trading account for user {user_id} on {exchange_id}")
                return False

            logger_main.info(f"Transferred {amount} {currency} to trading account for user {user_id} on {exchange_id}: transfer_id={transfer_result['id']}")

        return True
    except Exception as e:
        logger_main.error(f"Error managing deposit for user {user_id} on {exchange_id}: {e}")
        return False
    finally:
        await exchange.close()

__all__ = ['manage_deposit']
