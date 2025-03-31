import ccxt.async_support as ccxt
from logging_setup import logger_main
from symbol_handler import validate_symbol

async def create_order(exchange, symbol, side, amount, price=None, order_type='limit', params=None, exchange_id=None, user_id=None, testnet=False):
    """Creates an order on the exchange with optional parameters."""
    try:
        if not isinstance(exchange, ccxt.async_support.Exchange):
            logger_main.error(f"Exchange must be a ccxt.async_support.Exchange object, got {type(exchange)}")
            return None
        if not await validate_symbol(exchange_id, user_id, symbol, testnet=testnet):
            logger_main.error(f"Invalid symbol: {symbol}")
            return None
        if side not in ['buy', 'sell']:
            logger_main.error(f"Invalid side {side}: must be 'buy' or 'sell'")
            return None
        if order_type not in ['market', 'limit']:
            logger_main.error(f"Invalid order type {order_type}: must be 'market' or 'limit'")
            return None
        if amount <= 0:
            logger_main.error(f"Amount must be positive, got {amount}")
            return None

        if order_type == 'limit' and price is None:
            logger_main.error("Price must be specified for limit orders")
            return None

        # Use provided params or empty dict
        order_params = params if params is not None else {}

        if order_type == 'limit':
            order = await exchange.create_order(symbol, order_type, side, amount, price, order_params)
        else:
            order = await exchange.create_order(symbol, order_type, side, amount, params=order_params)

        logger_main.info(f"Created {order_type} {side} order for {symbol}: amount={amount}, price={price}, order_id={order.get('id', 'N/A')}, params={order_params}")
        return order
    except ccxt.NetworkError as e:
        logger_main.error(f"Network error while creating order for {symbol}: {e}")
        return None
    except ccxt.ExchangeError as e:
        logger_main.error(f"Exchange error while creating order for {symbol}: {e}")
        return None
    except Exception as e:
        logger_main.error(f"Error creating order for {symbol}: {e}")
        return None

__all__ = ['create_order']
