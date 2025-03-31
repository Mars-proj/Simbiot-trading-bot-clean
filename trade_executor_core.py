import ccxt.async_support as ccxt
import asyncio
from logging_setup import logger_main
from exchange_factory import create_exchange
from order_utils import create_order
from trade_executor_signals import process_signals
from limits import check_limits
from trade_pool_core import TradePool
from config_keys import MAX_LEVERAGE

async def execute_trade(exchange_id, user_id, symbol, signal, amount, leverage, order_type='limit', test_mode=False):
    """Executes a trade based on the signal, with specified amount, leverage, and order type."""
    try:
        # Validate input parameters
        if signal not in ['buy', 'sell']:
            logger_main.error(f"Invalid signal {signal}: must be 'buy' or 'sell'")
            return None
        if amount <= 0:
            logger_main.error(f"Invalid amount {amount}: must be positive")
            return None
        if leverage <= 0 or leverage > MAX_LEVERAGE:
            logger_main.error(f"Invalid leverage {leverage}: must be between 1 and {MAX_LEVERAGE}")
            return None
        if order_type not in ['market', 'limit']:
            logger_main.error(f"Invalid order type {order_type}: must be 'market' or 'limit'")
            return None

        # Create exchange instance
        exchange = create_exchange(exchange_id, user_id, testnet=test_mode)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return None

        # Fetch open trades
        trade_pool = TradePool(user_id, exchange_id)
        open_trades = await trade_pool.get_trades(exchange)
        if open_trades is None:
            logger_main.error(f"Failed to fetch open trades for user {user_id} on {exchange_id}")
            return None

        if not check_limits(amount, leverage, open_trades):
            logger_main.error(f"Trade limits exceeded for user {user_id} on {exchange_id}")
            return None

        # Fetch ticker to get current price
        ticker = await exchange.fetch_ticker(symbol)
        if not ticker:
            logger_main.error(f"Failed to fetch ticker for {symbol} on {exchange_id}")
            return None
        price = ticker['last']

        # Execute trade (in test mode, just log the action)
        if test_mode:
            logger_main.info(f"[Test Mode] Would execute {order_type} {signal} trade for user {user_id} on {exchange_id}: symbol={symbol}, amount={amount}, price={price}")
            return {"id": "test_order", "symbol": symbol, "amount": amount, "price": price}

        order = await create_order(exchange, symbol, signal, amount, price if order_type == 'limit' else None, order_type)
        if not order:
            logger_main.error(f"Failed to execute {signal} trade for {symbol} on {exchange_id}")
            return None

        # Save trade to trade pool
        await trade_pool.add_trade(order, exchange)
        logger_main.info(f"Executed {order_type} {signal} trade for user {user_id} on {exchange_id}: symbol={symbol}, amount={amount}, price={price}")
        return order
    except ccxt.NetworkError as e:
        logger_main.error(f"Network error while fetching ticker for {symbol} on {exchange_id}: {e}")
        return None
    except ccxt.ExchangeError as e:
        logger_main.error(f"Exchange error while fetching ticker for {symbol} on {exchange_id}: {e}")
        return None
    except Exception as e:
        logger_main.error(f"Error executing trade for {symbol} on {exchange_id}: {e}")
        return None
    finally:
        await exchange.close()

__all__ = ['execute_trade']
