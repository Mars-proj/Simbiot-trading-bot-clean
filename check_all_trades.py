from logging_setup import logger_main
from config_keys import SUPPORTED_EXCHANGES
from exchange_factory import create_exchange
from trade_pool_core import TradePool
from symbol_handler import validate_symbol

async def check_all_trades(exchange_id, user_id, status=None, testnet=False):
    """Checks all trades for a user on a specific exchange, optionally filtering by status."""
    try:
        if exchange_id not in SUPPORTED_EXCHANGES:
            logger_main.error(f"Exchange {exchange_id} not supported")
            return None

        # Create exchange instance
        exchange = create_exchange(exchange_id, user_id, testnet=testnet)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return None

        # Fetch trades from trade pool
        trade_pool = TradePool(user_id, exchange_id)
        trades = await trade_pool.get_trades(exchange)
        if trades is None:
            logger_main.error(f"Failed to fetch trades for user {user_id} on {exchange_id}")
            return None

        # Validate symbols in trades
        for trade in trades:
            symbol = trade.get('symbol')
            if symbol and not await validate_symbol(exchange_id, user_id, symbol, testnet=testnet):
                logger_main.warning(f"Invalid symbol in trade: {symbol}")
                trade['status'] = 'invalid_symbol'

        # Filter trades by status if specified
        if status:
            trades = [trade for trade in trades if trade.get('status') == status]

        # Log trade details
        for trade in trades:
            side = trade.get('side', 'N/A')
            amount = trade.get('amount', 'N/A')
            price = trade.get('price', 'N/A')
            trade_status = trade.get('status', 'N/A')
            logger_main.info(f"Trade for {trade['symbol']} on {exchange_id}: side={side}, amount={amount}, price={price}, status={trade_status}")

        logger_main.info(f"Checked {len(trades)} trades for user {user_id} on {exchange_id}")
        return trades
    except Exception as e:
        logger_main.error(f"Error checking trades for user {user_id} on {exchange_id}: {e}")
        return None
    finally:
        await exchange.close()

__all__ = ['check_all_trades']
