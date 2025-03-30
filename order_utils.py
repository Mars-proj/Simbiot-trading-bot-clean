import ccxt.async_support as ccxt
from logging_setup import logger_main

async def create_order(exchange, symbol, side, amount, price=None, order_type='limit'):
    """Creates an order on the exchange."""
    try:
        # Validate exchange
        if not isinstance(exchange, ccxt.async_support.BaseExchange):
            logger_main.error(f"Invalid exchange object: must be a ccxt.async_support.BaseExchange instance")
            return None

        # Validate parameters
        if side not in ['buy', 'sell']:
            logger_main.error(f"Invalid side {side}: must be 'buy' or 'sell'")
            return None
        if amount <= 0:
            logger_main.error(f"Invalid amount {amount}: must be positive")
            return None
        if order_type == 'limit' and (price is None or price <= 0):
            logger_main.error(f"Invalid price {price} for limit order: must be positive")
            return None

        # Create the order
        if order_type == 'market':
            order = await exchange.create_market_order(symbol, side, amount)
        else:
            order = await exchange.create_limit_order(symbol, side, amount, price)

        if not order:
            logger_main.error(f"Failed to create {order_type} {side} order for {symbol} on {exchange.id}")
            return None

        order_id = order.get('id', 'N/A')
        logger_main.info(f"Created {order_type} {side} order for {symbol} on {exchange.id}: order_id={order_id}, amount={amount}, price={price if price else 'N/A'}")
        return order
    except Exception as e:
        logger_main.error(f"Error creating order for {symbol} on {exchange.id}: {e}")
        return None

__all__ = ['create_order']
