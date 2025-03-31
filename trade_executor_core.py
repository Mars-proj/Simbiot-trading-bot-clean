import ccxt.async_support as ccxt
import asyncio
from logging_setup import logger_main
from exchange_factory import create_exchange
from order_utils import create_order
from trade_executor_signals import process_signals
from limits import check_limits
from trade_pool_core import TradePool
from config_keys import MAX_LEVERAGE
from exit_points_calculator import calculate_exit_points
from monetization import calculate_fee
from partial_close_calculator import calculate_partial_close
from risk_manager import calculate_risk
from balance_manager import BalanceManager
from symbol_handler import validate_symbol
from notification_manager import NotificationManager

async def execute_trade(exchange_id, user_id, symbol, signal, amount, leverage, order_type='limit', test_mode=False, stop_loss_percent=0.05, take_profit_percent=0.1, fee_rate=0.001, max_risk_percentage=0.02):
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
        if not await validate_symbol(exchange_id, user_id, symbol, testnet=test_mode):
            logger_main.error(f"Invalid symbol: {symbol}")
            return None

        # Create exchange instance
        exchange = create_exchange(exchange_id, user_id, testnet=test_mode)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return None

        # Fetch balance
        balance_manager = BalanceManager(user_id)
        balance = await balance_manager.get_balance(exchange)
        if not balance:
            logger_main.error(f"Failed to fetch balance for user {user_id} on {exchange_id}")
            return None
        currency = symbol.split('/')[1]  # e.g., USDT in BTC/USDT
        available_balance = balance.get(currency, {}).get('free', 0)

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

        # Calculate stop-loss and take-profit levels
        stop_loss, take_profit = calculate_exit_points(symbol, price, stop_loss_percent, take_profit_percent)
        if stop_loss is None or take_profit is None:
            logger_main.error(f"Failed to calculate exit points for {symbol}")
            return None

        # Calculate risk
        risk = calculate_risk(amount, leverage, stop_loss, price, available_balance, max_risk_percentage)
        if risk is None:
            logger_main.error(f"Risk calculation failed for {symbol}")
            return None

        # Calculate fee
        fee = calculate_fee(amount * price, fee_rate=fee_rate)
        if fee is None:
            logger_main.error(f"Failed to calculate fee for trade")
            return None

        # Execute trade (in test mode, just log the action)
        if test_mode:
            logger_main.info(f"[Test Mode] Would execute {order_type} {signal} trade for user {user_id} on {exchange_id}: symbol={symbol}, amount={amount}, price={price}, stop_loss={stop_loss}, take_profit={take_profit}, fee={fee}, risk={risk}")
            return {"id": "test_order", "symbol": symbol, "amount": amount, "price": price, "stop_loss": stop_loss, "take_profit": take_profit, "fee": fee, "risk": risk}

        order = await create_order(exchange, symbol, signal, amount, price if order_type == 'limit' else None, order_type)
        if not order:
            logger_main.error(f"Failed to execute {signal} trade for {symbol} on {exchange_id}")
            return None

        # Save trade to trade pool
        order['stop_loss'] = stop_loss
        order['take_profit'] = take_profit
        order['fee'] = fee
        order['risk'] = risk
        await trade_pool.add_trade(order, exchange)

        # Send notification
        notification_manager = NotificationManager()
        await notification_manager.notify(
            subject=f"Trade Executed: {symbol} on {exchange_id}",
            message=f"User {user_id} executed a {order_type} {signal} trade for {symbol} on {exchange_id}.\nAmount: {amount}\nPrice: {price}\nStop Loss: {stop_loss}\nTake Profit: {take_profit}\nFee: {fee}\nRisk: {risk}"
        )

        logger_main.info(f"Executed {order_type} {signal} trade for user {user_id} on {exchange_id}: symbol={symbol}, amount={amount}, price={price}, stop_loss={stop_loss}, take_profit={take_profit}, fee={fee}, risk={risk}")
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

async def close_partial_position(exchange_id, user_id, symbol, position_size, close_percentage=0.5, test_mode=False, fee_rate=0.001):
    """Closes a portion of an open position."""
    try:
        # Validate symbol
        if not await validate_symbol(exchange_id, user_id, symbol, testnet=test_mode):
            logger_main.error(f"Invalid symbol: {symbol}")
            return None

        # Calculate amount to close
        close_amount = calculate_partial_close(position_size, close_percentage)
        if close_amount is None:
            logger_main.error(f"Failed to calculate partial close amount for {symbol}")
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

        # Determine side (opposite of the original position)
        position = next((trade for trade in open_trades if trade['symbol'] == symbol), None)
        if not position:
            logger_main.error(f"No open position found for {symbol}")
            return None
        side = 'sell' if position['side'] == 'buy' else 'buy'

        # Fetch ticker to get current price
        ticker = await exchange.fetch_ticker(symbol)
        if not ticker:
            logger_main.error(f"Failed to fetch ticker for {symbol} on {exchange_id}")
            return None
        price = ticker['last']

        # Calculate fee
        fee = calculate_fee(close_amount * price, fee_rate=fee_rate)
        if fee is None:
            logger_main.error(f"Failed to calculate fee for partial close")
            return None

        # Execute partial close (in test mode, just log the action)
        if test_mode:
            logger_main.info(f"[Test Mode] Would close {close_percentage*100}% of position for user {user_id} on {exchange_id}: symbol={symbol}, close_amount={close_amount}, price={price}, fee={fee}")
            return {"id": "test_close", "symbol": symbol, "close_amount": close_amount, "price": price, "fee": fee}

        order = await create_order(exchange, symbol, side, close_amount, price, order_type='limit')
        if not order:
            logger_main.error(f"Failed to execute partial close for {symbol} on {exchange_id}")
            return None

        # Update trade in trade pool
        position['amount'] -= close_amount
        if position['amount'] <= 0:
            await trade_pool.remove_trade(position, exchange)
        else:
            await trade_pool.update_trade(position, exchange)

        # Send notification
        notification_manager = NotificationManager()
        await notification_manager.notify(
            subject=f"Partial Position Closed: {symbol} on {exchange_id}",
            message=f"User {user_id} closed {close_percentage*100}% of position for {symbol} on {exchange_id}.\nClose Amount: {close_amount}\nPrice: {price}\nFee: {fee}"
        )

        logger_main.info(f"Closed {close_percentage*100}% of position for user {user_id} on {exchange_id}: symbol={symbol}, close_amount={close_amount}, price={price}, fee={fee}")
        return order
    except ccxt.NetworkError as e:
        logger_main.error(f"Network error while closing position for {symbol} on {exchange_id}: {e}")
        return None
    except ccxt.ExchangeError as e:
        logger_main.error(f"Exchange error while closing position for {symbol} on {exchange_id}: {e}")
        return None
    except Exception as e:
        logger_main.error(f"Error closing position for {symbol} on {exchange_id}: {e}")
        return None
    finally:
        await exchange.close()

__all__ = ['execute_trade', 'close_partial_position']
