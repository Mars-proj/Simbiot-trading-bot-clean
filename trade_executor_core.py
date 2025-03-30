import ccxt.async_support as ccxt
import asyncio
from logging_setup import logger_main
from exchange_factory import create_exchange
from order_utils import create_order
from trade_executor_signals import process_signals
from limits import check_limits

async def execute_trade(exchange_id, user_id, symbol, signal, test_mode=False):
    """Executes a trade based on the signal, with optional test mode."""
    try:
        # Validate input parameters
        if signal not in ['buy', 'sell']:
            logger_main.error(f"Invalid signal {signal}: must be 'buy' or 'sell'")
            return None
        amount = 0.1  # Placeholder
        leverage = 1  # Placeholder
        if amount <= 0:
            logger_main.error(f"Invalid amount {amount}: must be positive")
            return None
        if leverage <= 0 or leverage > 5:  # Assuming max leverage is 5
            logger_main.error(f"Invalid leverage {leverage}: must be between 1 and 5")
            return None

        # Create exchange instance
        exchange = create_exchange(exchange_id, user_id, testnet=test_mode)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return None

        # Fetch open trades (placeholder)
        open_trades = []  # This should be fetched from trade_pool_core or similar
        if not check_limits(amount, leverage, open_trades):
            logger_main.error(f"Trade limits exceeded for user {user_id} on {exchange_id}")
            return None

        # Fetch ticker to get current price
        ticker = await exchange.fetch_ticker(symbol)
        if not ticker:
            logger_main.error(f"Failed to fetch ticker for {symbol} on {exchange_id}")
            return None
        price = ticker['last']

        # Determine order type (placeholder logic)
        order_type = 'market' if signal == 'buy' else 'limit'

        # Execute trade (in test mode, just log the action)
        if test_mode:
            logger_main.info(f"[Test Mode] Would execute {order_type} {signal} trade for user {user_id} on {exchange_id}: symbol={symbol}, amount={amount}, price={price}")
            return {"id": "test_order", "symbol": symbol, "amount": amount, "price": price}

        order = await create_order(exchange, symbol, signal, amount, price if order_type == 'limit' else None, order_type)
        if not order:
            logger_main.error(f"Failed to execute {signal} trade for {symbol} on {exchange_id}")
            return None

        logger_main.info(f"Executed {signal} trade for user {user_id} on {exchange_id}: symbol={symbol}, amount={amount}, price={price}")
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
