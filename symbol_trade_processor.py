from logging_setup import logger_main
from exchange_factory import create_exchange
from trade_pool_core import TradePool
from trade_executor_core import close_partial_position
from symbol_handler import validate_symbol
from config_keys import SUPPORTED_EXCHANGES

async def process_symbol_trades(exchange_id, user_id, symbol, testnet=False, loss_threshold=-0.1):
    """Processes trades for a specific symbol, closing positions with significant losses."""
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

        # Filter trades for the symbol
        symbol_trades = [trade for trade in open_trades if trade['symbol'] == symbol]
        if not symbol_trades:
            logger_main.info(f"No open trades found for {symbol} for user {user_id} on {exchange_id}")
            return True

        # Fetch current price
        ticker = await exchange.fetch_ticker(symbol)
        if not ticker:
            logger_main.error(f"Failed to fetch ticker for {symbol} on {exchange_id}")
            return False
        current_price = ticker['last']

        # Process each trade
        for trade in symbol_trades:
            entry_price = trade.get('price', 0)
            side = trade['side']
            amount = trade['amount']

            # Calculate profit/loss percentage
            if side == 'buy':
                profit_loss = (current_price - entry_price) / entry_price
            else:  # sell
                profit_loss = (entry_price - current_price) / entry_price

            # Check if loss exceeds threshold
            if profit_loss < loss_threshold:
                logger_main.info(f"Loss threshold exceeded for {symbol}: profit/loss={profit_loss*100:.2f}%, closing position")
                order = await close_partial_position(exchange_id, user_id, symbol, amount, close_percentage=1.0, test_mode=testnet)
                if not order:
                    logger_main.error(f"Failed to close position for {symbol}")
                    return False
            else:
                logger_main.info(f"Trade for {symbol} within acceptable loss: profit/loss={profit_loss*100:.2f}%")

        logger_main.info(f"Processed {len(symbol_trades)} trades for {symbol} for user {user_id} on {exchange_id}")
        return True
    except Exception as e:
        logger_main.error(f"Error processing trades for {symbol} on {exchange_id}: {e}")
        return False
    finally:
        await exchange.close()

__all__ = ['process_symbol_trades']
