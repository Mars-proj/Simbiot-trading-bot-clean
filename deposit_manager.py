import ccxt.async_support as ccxt
import asyncio
from logging_setup import logger_main
from config_keys import API_KEYS, SUPPORTED_EXCHANGES, validate_api_keys
from bot_user_data import user_data
from deposit_calculator import calculate_deposit
from symbol_handler import validate_symbol_with_markets

async def manage_deposit(exchange_id, user_id, symbol, amount):
    """Manages deposits for a user on the specified exchange."""
    try:
        # Validate exchange ID
        if exchange_id not in SUPPORTED_EXCHANGES:
            logger_main.error(f"Exchange {exchange_id} not supported for user {user_id}")
            return None

        # Validate user ID
        if user_id not in user_data:
            logger_main.error(f"User {user_id} not found in user_data")
            return None

        # Validate API keys
        api_key = API_KEYS.get(user_id, {}).get(exchange_id, {}).get("api_key")
        api_secret = API_KEYS.get(user_id, {}).get(exchange_id, {}).get("api_secret")
        if not validate_api_keys(api_key, api_secret):
            logger_main.error(f"API keys for {exchange_id} failed validation for user {user_id}")
            return None

        # Create exchange instance
        exchange_class = getattr(ccxt, exchange_id)
        exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })

        # Validate symbol
        if not await validate_symbol_with_markets(exchange, symbol):
            return None

        # Calculate required deposit
        required_deposit = calculate_deposit(symbol, amount)
        if required_deposit is None:
            logger_main.error(f"Failed to calculate deposit for {symbol} with amount {amount}")
            return None

        # Fetch balance
        balance = await exchange.fetch_balance()
        if not balance:
            logger_main.error(f"Failed to fetch balance for user {user_id} on {exchange_id}")
            return None

        # Extract currency from symbol (e.g., USDT from BTC/USDT)
        currency = symbol.split('/')[1]
        total_balance = balance.get(currency, {}).get('total', 0)

        # Log balance and deposit info
        logger_main.info(f"Managing deposit for user {user_id} on {exchange_id}: symbol={symbol}, currency={currency}, total_balance={total_balance}, required_deposit={required_deposit}")

        # Check if deposit is sufficient
        if total_balance < required_deposit:
            logger_main.warning(f"Insufficient balance for user {user_id} on {exchange_id}: required {required_deposit}, available {total_balance}")
            return None

        return required_deposit
    except Exception as e:
        logger_main.error(f"Error managing deposit for {user_id} on {exchange_id} for {symbol}: {e}")
        return None
    finally:
        await exchange.close()

__all__ = ['manage_deposit']
