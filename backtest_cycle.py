from logging_setup import logger_main
from bot_trading import run_trading_bot
from historical_data_fetcher import fetch_historical_data

async def run_backtest(exchange_id, user_id, symbol, start_timestamp, end_timestamp, leverage=1.0, order_type='limit', trade_percentage=0.1, rsi_overbought=70, rsi_oversold=30, margin_multiplier=2.0, blacklisted_symbols=None, model_path=None):
    """Runs a backtest for a specific symbol over a given time period."""
    try:
        # Fetch historical data
        historical_data = await fetch_historical_data(exchange_id, user_id, symbol, timeframe='1h', since=start_timestamp, limit=1000)
        if historical_data is None or historical_data.empty:
            logger_main.error(f"Failed to fetch historical data for {symbol} on {exchange_id}")
            return False

        # Filter data within the specified time range
        historical_data = historical_data[
            (historical_data['timestamp'] >= pd.Timestamp.fromtimestamp(start_timestamp)) &
            (historical_data['timestamp'] <= pd.Timestamp.fromtimestamp(end_timestamp))
        ]

        if historical_data.empty:
            logger_main.warning(f"No historical data available for {symbol} in the specified time range")
            return False

        # Simulate trading over historical data
        trades = []
        for _, row in historical_data.iterrows():
            # Simulate OHLCV data for the current timestamp
            ohlcv = {
                'timestamp': [row['timestamp'].timestamp() * 1000],
                'open': [row['open']],
                'high': [row['high']],
                'low': [row['low']],
                'close': [row['close']],
                'volume': [row['volume']]
            }

            # Run trading bot with simulated data
            result = await run_trading_bot(
                exchange_id, user_id, symbol,
                leverage=leverage,
                order_type=order_type,
                trade_percentage=trade_percentage,
                rsi_overbought=rsi_overbought,
                rsi_oversold=rsi_oversold,
                margin_multiplier=margin_multiplier,
                blacklisted_symbols=blacklisted_symbols,
                model_path=model_path,
                test_mode=True  # Always in test mode for backtesting
            )

            if result:
                trades.append({
                    'timestamp': row['timestamp'],
                    'price': row['close'],
                    'action': 'buy' if result else 'sell'  # Simplified for backtesting
                })

        logger_main.info(f"Backtest completed for {symbol} on {exchange_id}: {len(trades)} trades executed")
        return trades
    except Exception as e:
        logger_main.error(f"Error running backtest for {symbol} on {exchange_id}: {e}")
        return False

__all__ = ['run_backtest']
