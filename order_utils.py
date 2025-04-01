from logging_setup import logger_main
from symbol_handler import validate_symbol

async def create_order(exchange, symbol, side, amount, price=None, order_type='limit', params=None):
    """Creates an order on the exchange."""
    try:
        # Validate symbol
        if not await validate_symbol(exchange.id, exchange.user_id, symbol, testnet=exchange.testnet):
            logger_main.error(f"Invalid symbol: {symbol}")
            return None

        # Prepare order parameters
        order_params = params or {}
        if order_type == 'limit' and price is None:
            logger_main.error(f"Price is required for limit order on {symbol}")
            return None

        # Create the order
        if order_type == 'limit':
            order = await exchange.create_limit_order(symbol, side, amount, price, order_params)
        else:
            order = await exchange.create_market_order(symbol, side, amount, order_params)

        if not order or 'id' not in order:
            logger_main.error(f"Failed to create {order_type} {side} order for {symbol} on {exchange.id}")
            return None

        logger_main.info(f"Created {order_type} {side} order for {symbol} on {exchange.id}: order_id={order['id']}, amount={amount}, price={price}")
        return order
    except Exception as e:
        logger_main.error(f"Error creating order for {symbol} on {exchange.id}: {e}")
        return None

async def cancel_order(exchange, symbol, order_id):
    """Cancels an order on the exchange."""
    try:
        # Validate symbol
        if not await validate_symbol(exchange.id, exchange.user_id, symbol, testnet=exchange.testnet):
            logger_main.error(f"Invalid symbol: {symbol}")
            return False

        # Cancel the order
        result = await exchange.cancel_order(order_id, symbol)
        if not result:
            logger_main.error(f"Failed to cancel order {order_id} for {symbol} on {exchange.id}")
            return False

        logger_main.info(f"Cancelled order {order_id} for {symbol} on {exchange.id}")
        return True
    except Exception as e:
        logger_main.error(f"Error cancelling order {order_id} for {symbol} on {exchange.id}: {e}")
        return False

__all__ = ['create_order', 'cancel_order']
