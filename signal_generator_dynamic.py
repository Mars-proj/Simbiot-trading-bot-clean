from logging_setup import logger_main
from ohlcv_fetcher import fetch_ohlcv
from signal_generator_indicators import calculate_rsi, calculate_macd

async def generate_dynamic_signals(exchange_id, user_id, symbol, timeframe='1h', limit=100, testnet=False, exchange=None):
    """Generates dynamic trading signals based on market conditions."""
    try:
        # Получить OHLCV-данные
        ohlcv_data = await fetch_ohlcv(exchange_id, symbol, user_id, timeframe, limit, testnet, exchange)
        if ohlcv_data is None or ohlcv_data.empty:
            logger_main.debug(f"Failed to fetch OHLCV data for {symbol} on {exchange_id}")
            return None

        # Рассчитать индикаторы
        rsi = calculate_rsi(ohlcv_data['close'])
        macd, signal_line = calculate_macd(ohlcv_data['close'])

        # Динамические пороговые значения
        market_volatility = ohlcv_data['close'].pct_change().std() * 100
        rsi_overbought = 70 - (market_volatility * 2)  # Пример адаптации
        rsi_oversold = 30 + (market_volatility * 2)

        # Генерация сигнала
        latest_rsi = rsi.iloc[-1]
        latest_macd = macd.iloc[-1]
        latest_signal = signal_line.iloc[-1]

        if latest_rsi > rsi_overbought and latest_macd < latest_signal:
            signal = "sell"
        elif latest_rsi < rsi_oversold and latest_macd > latest_signal:
            signal = "buy"
        else:
            signal = "hold"

        logger_main.debug(f"Generated signal for {symbol}: {signal} (RSI: {latest_rsi}, MACD: {latest_macd}, Signal Line: {latest_signal})")
        return signal
    except Exception as e:
        logger_main.error(f"Error generating dynamic signals for {symbol} on {exchange_id}: {e}")
        return None

__all__ = ['generate_dynamic_signals']
