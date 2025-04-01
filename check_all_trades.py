from logging_setup import logger_main
from config_keys import API_KEYS, validate_api_keys
from symbol_handler import validate_symbol
from exchange_factory import create_exchange
from trade_pool_core import TradePool

async def check_all_trades(exchange_id, user_id, symbols, testnet=False, status_filter=None):
    """Checks all trades for a user on a specific exchange, with optional status filter."""
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

        # Validate symbols
        for symbol in symbols:
            if not await validate_symbol(exchange_id, user_id, symbol, testnet=testnet):
                logger_main.error(f"Invalid symbol: {symbol}")
                return False

        # Create exchange instance
        exchange = create_exchange(exchange_id, user_id, testnet=testnet)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return False

        # Fetch trades using trade_pool_core
        trade_pool = TradePool(user_id, exchange_id)
        trades = await trade_pool.get_trades(exchange)
        if trades is None:
            logger_main.error(f"Failed to fetch trades for user {user_id} on {exchange_id}")
            return False

        # Filter trades by status if specified
        if status_filter:
            trades = [trade for trade in trades if trade.get('status', 'open') == status_filter]

        for trade in trades:
            logger_main.info(f"Trade for {trade.get('symbol', 'N/A')}: type={trade.get('type', 'N/A')}, amount={trade.get('amount', 'N/A')}, status={trade.get('status', 'open')}")
        logger_main.info(f"Checked {len(trades)} trades for user {user_id} on {exchange_id}")
        return True
    except Exception as e:
        logger_main.error(f"Error checking trades for user {user_id} on {exchange_id}: {e}")
        return False
    finally:
        await exchange.close()

__all__ = ['check_all_trades']
