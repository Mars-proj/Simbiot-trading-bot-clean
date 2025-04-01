import pandas as pd
from logging_setup import logger_main
from bot_trading import run_trading_bot
from historical_data_fetcher import fetch_historical_data
import os

async def run_backtest(exchange_id, user_id, symbol, start_timestamp, end_timestamp, timeframe='1d', leverage=1.0, order_type='limit', trade_percentage=0.1, rsi_overbought=70, rsi_oversold=30, margin_multiplier=2.0, model_path=None):
    """Runs a backtest for a given symbol over a specified time period."""
    try:
        # Fetch historical data
        historical_data = await fetch_historical_data(exchange_id, user_id, symbol, timeframe=timeframe, since=start_timestamp, testnet=True)
        if historical_data is None or historical_data.empty:
            logger_main.error(f"Failed to fetch historical data for {symbol} on {exchange_id}")
            return None

        # Filter data within the specified time range
        historical_data = historical_data[(historical_data['timestamp'] >= pd.Timestamp.fromtimestamp(start_timestamp)) & (historical_data['timestamp'] <= pd.Timestamp.fromtimestamp(end_timestamp))]
        if historical_data.empty:
            logger_main.error(f"No historical data available for {symbol} between {start_timestamp} and {end_timestamp}")
            return None

        # Simulate trading
        trades = []
        for _, row in historical_data.iterrows():
            # Simulate a single trading cycle at each timestamp
            result = await run_trading_bot(
                exchange_id, user_id, symbol,
                leverage=leverage,
                order_type=order_type,
                trade_percentage=trade_percentage,
                rsi_overbought=rsi_overbought,
                rsi_oversold=rsi_oversold,
                margin_multiplier=margin_multiplier,
                model_path=model_path,
                test_mode=True
            )
            if result:
                trades.append({
                    'timestamp': row['timestamp'],
                    'price': row['close'],
                    'action': 'executed' if result else 'skipped'
                })

        # Convert trades to DataFrame
        trades_df = pd.DataFrame(trades)
        
        # Save results to a file
        os.makedirs('backtest_results', exist_ok=True)
        result_file = f"backtest_results/{exchange_id}_{symbol}_{start_timestamp}_{end_timestamp}.csv"
        trades_df.to_csv(result_file, index=False)
        logger_main.info(f"Backtest completed for {symbol} on {exchange_id}. Results saved to {result_file}")

        return trades_df
    except Exception as e:
        logger_main.error(f"Error running backtest for {symbol} on {exchange_id}: {e}")
        return None

__all__ = ['run_backtest']
