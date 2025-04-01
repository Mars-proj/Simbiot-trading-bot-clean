from logging_setup import logger_main
from symbol_handler import validate_symbol

async def create_order(exchange, symbol, side, amount, price=None, order_type='limit'):
    """Creates an order on the exchange."""
    try:
        if not await validate_symbol(exchange.id, exchange.user_id, symbol, testnet=exchange.testnet):
            logger_main.error(f"Invalid symbol: {symbol}")
            return None
        if side not in ['buy', 'sell']:
            logger_main.error(f"Invalid side: {side}")
            return None
        if amount <= 0:
            logger_main.error(f"Invalid amount: {amount}")
            return None
        if order_type not in ['market', 'limit']:
            logger_main.error(f"Invalid order type: {order_type}")
            return None
        if order_type == 'limit' and (price is None or price <= 0):
            logger_main.error(f"Invalid price for limit order: {price}")
            return None

        # Create order
        if order_type == 'limit':
            order = await exchange.create_limit_order(symbol, side, amount, price)
        else:
            order = await exchange.create_market_order(symbol, side, amount)

        order_id = order.get('id', 'N/A')
        logger_main.info(f"Created {order_type} {side} order for {symbol} on {exchange.id}: amount={amount}, price={price}, order_id={order_id}")
        return order
    except Exception as e:
        logger_main.error(f"Error creating order for {symbol} on {exchange.id}: {e}")
        return None

async def cancel_order(exchange, symbol, order_id):
    """Cancels an order on the exchange."""
    try:
        if not await validate_symbol(exchange.id, exchange.user_id, symbol, testnet=exchange.testnet):
            logger_main.error(f"Invalid symbol: {symbol}")
            return False

        await exchange.cancel_order(order_id, symbol)
        logger_main.info(f"Cancelled order {order_id} for {symbol} on {exchange.id}")
        return True
    except Exception as e:
        logger_main.error(f"Error cancelling order {order_id} for {symbol} on {exchange.id}: {e}")
        return False

__all__ = ['create_order', 'cancel_order']
