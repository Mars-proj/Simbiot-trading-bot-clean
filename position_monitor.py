from logging_setup import logger_main
from exchange_factory import create_exchange
from trade_pool_core import TradePool
from trade_executor_core import close_partial_position
from symbol_handler import validate_symbol

async def monitor_positions(exchange_id, user_id, testnet=False):
    """Monitors open positions and triggers stop-loss/take-profit if conditions are met."""
    try:
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

        if not open_trades:
            logger_main.info(f"No open positions for user {user_id} on {exchange_id}")
            return True

        for trade in open_trades:
            symbol = trade.get('symbol')
            if not symbol:
                logger_main.error(f"Trade missing symbol: {trade}")
                continue

            # Validate symbol
            if not await validate_symbol(exchange_id, user_id, symbol, testnet=testnet):
                logger_main.error(f"Invalid symbol: {symbol}")
                continue

            # Fetch current price
            ticker = await exchange.fetch_ticker(symbol)
            if not ticker:
                logger_main.error(f"Failed to fetch ticker for {symbol} on {exchange_id}")
                continue
            current_price = ticker.get('last')
            if current_price is None or current_price <= 0:
                logger_main.error(f"Invalid price for {symbol} on {exchange_id}: {current_price}")
                continue

            # Check stop-loss and take-profit
            stop_loss = trade.get('stop_loss')
            take_profit = trade.get('take_profit')
            position_size = trade.get('amount', 0)

            if stop_loss and current_price <= stop_loss:
                logger_main.info(f"Stop-loss triggered for {symbol} on {exchange_id}: current_price={current_price}, stop_loss={stop_loss}")
                if testnet:
                    logger_main.info(f"[Test Mode] Would close position for {symbol} at stop-loss")
                else:
                    await close_partial_position(exchange_id, user_id, symbol, position_size, close_percentage=1.0, testnet=testnet)
                continue

            if take_profit and current_price >= take_profit:
                logger_main.info(f"Take-profit triggered for {symbol} on {exchange_id}: current_price={current_price}, take_profit={take_profit}")
                if testnet:
                    logger_main.info(f"[Test Mode] Would close position for {symbol} at take-profit")
                else:
                    await close_partial_position(exchange_id, user_id, symbol, position_size, close_percentage=1.0, testnet=testnet)
                continue

        logger_main.info(f"Monitored {len(open_trades)} open positions for user {user_id} on {exchange_id}")
        return True
    except Exception as e:
        logger_main.error(f"Error monitoring positions for user {user_id} on {exchange_id}: {e}")
        return False
    finally:
        await exchange.close()

__all__ = ['monitor_positions']
