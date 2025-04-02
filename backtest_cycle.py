from logging_setup import logger_main
from ohlcv_fetcher import fetch_ohlcv
from signal_generator_indicators import calculate_rsi
import time

async def run_backtest(exchange_id, user_id, symbol, days=30, leverage=1.0, trade_percentage=0.1, rsi_overbought=70, rsi_oversold=30, test_mode=False):
    """Runs a backtest for a given symbol."""
    try:
        logger_main.info(f"Starting backtest for {symbol} on {exchange_id} for user {user_id}")
        
        # Fetch historical data for the past 'days'
        since = int(time.time() * 1000) - (days * 24 * 60 * 60 * 1000)  # Convert days to milliseconds
        ohlcv_data = await fetch_ohlcv(exchange_id, symbol, user_id, timeframe='1h', limit=days*24, testnet=test_mode)
        if ohlcv_data is None or ohlcv_data.empty:
            logger_main.error(f"Failed to fetch historical data for {symbol} on {exchange_id}")
            return None

        # Simulate trading
        initial_balance = 1000.0  # Starting balance in USDT
        balance = initial_balance
        position = 0.0  # Amount of the asset held
        trades = []

        rsi = calculate_rsi(ohlcv_data['close'])
        if rsi is None:
            logger_main.error(f"Failed to calculate RSI for {symbol}")
            return None

        for i in range(1, len(ohlcv_data)):
            current_price = ohlcv_data['close'].iloc[i]
            current_rsi = rsi.iloc[i]

            # Buy signal
            if current_rsi < rsi_oversold and balance > 0:
                amount_to_buy = (balance * trade_percentage * leverage) / current_price
                position += amount_to_buy
                balance -= amount_to_buy * current_price
                trades.append({'type': 'buy', 'price': current_price, 'amount': amount_to_buy, 'timestamp': ohlcv_data['timestamp'].iloc[i]})
                logger_main.debug(f"Backtest buy: {amount_to_buy} of {symbol} at {current_price}, balance={balance}")

            # Sell signal
            elif current_rsi > rsi_overbought and position > 0:
                balance += position * current_price
                trades.append({'type': 'sell', 'price': current_price, 'amount': position, 'timestamp': ohlcv_data['timestamp'].iloc[i]})
                logger_main.debug(f"Backtest sell: {position} of {symbol} at {current_price}, balance={balance}")
                position = 0.0

        # Calculate final profit
        if position > 0:
            balance += position * ohlcv_data['close'].iloc[-1]  # Close position at the last price
        profit = (balance - initial_balance) / initial_balance

        result = {
            'profit': profit,
            'trades': trades,
            'final_balance': balance
        }
        logger_main.info(f"Backtest completed for {symbol}: profit={profit:.2%}, final_balance={balance}")
        return result
    except Exception as e:
        logger_main.error(f"Error in backtest for {symbol} on {exchange_id}: {e}")
        return None

__all__ = ['run_backtest']
