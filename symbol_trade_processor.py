from logging_setup import logger_main
from exchange_factory import create_exchange
from trade_pool_core import TradePool
from trade_executor_core import close_partial_position
from symbol_handler import validate_symbol

async def process_symbol_trades(exchange_id, user_id, symbol, loss_threshold=0.1, testnet=False):
    """Processes trades for a specific symbol, closing positions if loss exceeds threshold."""
    try:
        # Create exchange instance
        exchange = create_exchange(exchange_id, user_id, testnet=testnet)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return False

        # Validate symbol
        if not await validate_symbol(exchange_id, user_id, symbol, testnet=testnet):
            logger_main.error(f"Invalid symbol: {symbol}")
            return False

        # Fetch open trades
        trade_pool = TradePool(user_id, exchange_id)
        open_trades = await trade_pool.get_trades(exchange)
        if open_trades is None:
            logger_main.error(f"Failed to fetch open trades for user {user_id} on {exchange_id}")
            return False

        # Filter trades for the specific symbol
        symbol_trades = [trade for trade in open_trades if trade['symbol'] == symbol]
        if not symbol_trades:
            logger_main.info(f"No open trades for {symbol} on {exchange_id}")
            return True

        # Fetch current price
        ticker = await exchange.fetch_ticker(symbol)
        if not ticker:
            logger_main.error(f"Failed to fetch ticker for {symbol} on {exchange_id}")
            return False
        current_price = ticker.get('last')
        if current_price is None or current_price <= 0:
            logger_main.error(f"Invalid price for {symbol} on {exchange_id}: {current_price}")
            return False

        # Process each trade
        for trade in symbol_trades:
            entry_price = trade.get('price')
            position_size = trade.get('amount')
            if entry_price is None or position_size is None:
                logger_main.error(f"Invalid trade data for {symbol}: entry_price={entry_price}, position_size={position_size}")
                continue

            # Calculate loss percentage
            loss_percentage = (entry_price - current_price) / entry_price if trade['side'] == 'buy' else (current_price - entry_price) / entry_price
            if loss_percentage >= loss_threshold:
                logger_main.info(f"Loss threshold ({loss_percentage:.2%}) exceeded for {symbol} on {exchange_id}, closing position")
                await close_partial_position(exchange_id, user_id, symbol, position_size, close_percentage=1.0, test_mode=testnet)

        logger_main.info(f"Processed {len(symbol_trades)} trades for {symbol} on {exchange_id}")
        return True
    except Exception as e:
        logger_main.error(f"Error processing trades for {symbol} on {exchange_id}: {e}")
        return False
    finally:
        await exchange.close()

__all__ = ['process_symbol_trades']
