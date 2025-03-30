import ccxt.async_support as ccxt
import asyncio
from logging_setup import logger_main
from config_keys import API_KEYS, SUPPORTED_EXCHANGES, validate_api_keys
from bot_user_data import user_data
from trade_pool_queries import get_all_trades
from symbol_handler import validate_symbol_with_markets

async def check_all_trades(exchange_id, user_id, symbol=None):
    """Checks all trades for a user on the specified exchange, with optional symbol filtering."""
    try:
        # Validate exchange ID
        if exchange_id not in SUPPORTED_EXCHANGES:
            logger_main.error(f"Exchange {exchange_id} not supported for user {user_id}")
            return []

        # Validate user ID
        if user_id not in user_data:
            logger_main.error(f"User {user_id} not found in user_data")
            return []

        # Validate API keys
        api_key = API_KEYS.get(user_id, {}).get(exchange_id, {}).get("api_key")
        api_secret = API_KEYS.get(user_id, {}).get(exchange_id, {}).get("api_secret")
        if not validate_api_keys(api_key, api_secret):
            logger_main.error(f"API keys for {exchange_id} failed validation for user {user_id}")
            return []

        # Create exchange instance
        exchange_class = getattr(ccxt, exchange_id)
        exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })

        # Validate symbol if provided
        if symbol:
            if not await validate_symbol_with_markets(exchange, symbol):
                return []
            trades = await exchange.fetch_my_trades(symbol)
        else:
            trades = await get_all_trades(exchange, user_id)

        # Validate trades data
        if not isinstance(trades, list):
            logger_main.error(f"Invalid trades format for {user_id} on {exchange_id}")
            return []

        # Log trade types
        if trades:
            buy_trades = sum(1 for trade in trades if trade.get('side') == 'buy')
            sell_trades = sum(1 for trade in trades if trade.get('side') == 'sell')
            logger_main.info(f"Checked {len(trades)} trades for user {user_id} on {exchange_id}" + (f" for symbol {symbol}" if symbol else "") + f": {buy_trades} buy, {sell_trades} sell")
        else:
            logger_main.warning(f"No trades found for user {user_id} on {exchange_id}" + (f" for symbol {symbol}" if symbol else ""))

        return trades
    except Exception as e:
        logger_main.error(f"Error checking trades for {user_id} on {exchange_id}" + (f" for symbol {symbol}" if symbol else "") + f": {e}")
        return []
    finally:
        await exchange.close()

__all__ = ['check_all_trades']
