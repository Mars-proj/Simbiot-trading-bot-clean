from logging_setup import logger_main
from bot_trading import run_trading_bot

async def run_backtest(exchange_id, user_id, symbols, start_time, end_time, leverage=1.0, order_type='limit', trade_percentage=0.1, rsi_overbought=70, rsi_oversold=30, margin_multiplier=2.0, blacklisted_symbols=None, test_mode=True):
    """Runs a backtest cycle for the specified symbols and time range."""
    try:
        logger_main.info(f"Starting backtest for user {user_id} on {exchange_id} from {start_time} to {end_time}")
        # Simulate historical data fetching (placeholder)
        for symbol in symbols:
            logger_main.info(f"Simulating historical data for {symbol} from {start_time} to {end_time}")
            result = await run_trading_bot(
                exchange_id, user_id, symbol,
                leverage=leverage,
                order_type=order_type,
                trade_percentage=trade_percentage,
                rsi_overbought=rsi_overbought,
                rsi_oversold=rsi_oversold,
                margin_multiplier=margin_multiplier,
                blacklisted_symbols=blacklisted_symbols,
                test_mode=test_mode
            )
            if result:
                logger_main.info(f"Backtest successful for {symbol}")
            else:
                logger_main.warning(f"Backtest failed for {symbol}")
        logger_main.info(f"Completed backtest for user {user_id} on {exchange_id}")
        return True
    except Exception as e:
        logger_main.error(f"Error running backtest for user {user_id} on {exchange_id}: {e}")
        return False

__all__ = ['run_backtest']
