from logging_setup import logger_main
from exchange_factory import create_exchange
from trade_pool_core import TradePool
from trade_executor_core import close_partial_position
from symbol_handler import validate_symbol
from config_keys import SUPPORTED_EXCHANGES

async def monitor_positions(exchange_id, user_id, symbol, testnet=False):
    """Monitors open positions for a user and triggers actions based on stop-loss/take-profit."""
    try:
        # Validate inputs
        if exchange_id not in SUPPORTED_EXCHANGES:
            logger_main.error(f"Exchange {exchange_id} not supported")
            return False
        if not user_id or not isinstance(user_id, str):
            logger_main.error(f"Invalid user_id: {user_id}")
            return False
        if not await validate_symbol(exchange_id, user_id, symbol, testnet=testnet):
            logger_main.error(f"Invalid symbol: {symbol}")
            return False

        # Create exchange instance
        exchange = create_exchange(exchange_id, user_id, testnet=testnet)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return False

        # Fetch open trades
        trade_pool = TradePool(user_id, exchange_id)
        open_trades = await trade_pool.get_trades(exchange)
        if open_trades is None:
            logger_main.error(f"Failed to fetch open trades for user {user_id} on {exchange_id}")
            return False

        # Find position for the symbol
        position = next((trade for trade in open_trades if trade['symbol'] == symbol), None)
        if not position:
            logger_main.info(f"No open position found for {symbol} for user {user_id} on {exchange_id}")
            return True

        # Fetch current price
        ticker = await exchange.fetch_ticker(symbol)
        if not ticker:
            logger_main.error(f"Failed to fetch ticker for {symbol} on {exchange_id}")
            return False
        current_price = ticker['last']

        # Check stop-loss and take-profit
        stop_loss = position.get('stop_loss')
        take_profit = position.get('take_profit')
        position_size = position['amount']
        side = position['side']

        action_taken = False
        if stop_loss and ((side == 'buy' and current_price <= stop_loss) or (side == 'sell' and current_price >= stop_loss)):
            logger_main.info(f"Stop-loss triggered for {symbol}: current_price={current_price}, stop_loss={stop_loss}")
            # Close the entire position
            order = await close_partial_position(exchange_id, user_id, symbol, position_size, close_percentage=1.0, test_mode=testnet)
            if not order:
                logger_main.error(f"Failed to close position at stop-loss for {symbol}")
                return False
            action_taken = True

        elif take_profit and ((side == 'buy' and current_price >= take_profit) or (side == 'sell' and current_price <= take_profit)):
            logger_main.info(f"Take-profit triggered for {symbol}: current_price={current_price}, take_profit={take_profit}")
            # Close the entire position
            order = await close_partial_position(exchange_id, user_id, symbol, position_size, close_percentage=1.0, test_mode=testnet)
            if not order:
                logger_main.error(f"Failed to close position at take-profit for {symbol}")
                return False
            action_taken = True

        if not action_taken:
            logger_main.info(f"No action taken for {symbol}: current_price={current_price}, stop_loss={stop_loss}, take_profit={take_profit}")

        return True
    except Exception as e:
        logger_main.error(f"Error monitoring positions for user {user_id} on {exchange_id}: {e}")
        return False
    finally:
        await exchange.close()

__all__ = ['monitor_positions']
