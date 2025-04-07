# start_trading_all.py
import logging
import numpy as np
import pandas as pd

logger = logging.getLogger("main")

async def calculate_rsi(exchange, symbol, timeframe='4h', period=14, limit=100):
    """Вычисляет RSI для символа."""
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        if not ohlcv or len(ohlcv) < period:
            logger.warning(f"Insufficient data to calculate RSI for {symbol}")
            return None

        # Извлекаем цены закрытия
        closes = [candle[4] for candle in ohlcv]
        df = pd.Series(closes)

        # Вычисляем изменения цен
        delta = df.diff()

        # Разделяем на приросты и убытки
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        # Вычисляем RS и RSI
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # Возвращаем последнее значение RSI
        return rsi.iloc[-1]
    except Exception as e:
        logger.error(f"Failed to calculate RSI for {symbol}: {type(e).__name__}: {str(e)}")
        return None

async def start_trading_all(exchange, valid_symbols, user):
    logger.debug(f"Exchange instance received: {exchange}")
    logger.debug(f"Exchange methods available: {dir(exchange)}")
    logger.info(f"Starting trading for user {user} with {len(valid_symbols)} symbols: {valid_symbols}")

    for symbol in valid_symbols:
        try:
            # Вычисляем RSI
            rsi = await calculate_rsi(exchange, symbol)
            if rsi is None:
                logger.warning(f"Skipping {symbol} due to insufficient RSI data")
                continue

            logger.info(f"RSI for {symbol}: {rsi}")

            # Простая стратегия: покупаем, если RSI < 30 (перепроданность), продаём, если RSI > 70 (перекупленность)
            if rsi < 30:
                logger.debug(f"Placing market buy order for {symbol} with amount 5 (RSI: {rsi})")
                order = await exchange.create_market_buy_order(symbol, 5)
                logger.info(f"Buy trade executed for {symbol} on mexc: {order}")
            elif rsi > 70:
                logger.debug(f"Placing market sell order for {symbol} with amount 5 (RSI: {rsi})")
                order = await exchange.create_market_sell_order(symbol, 5)
                logger.info(f"Sell trade executed for {symbol} on mexc: {order}")
            else:
                logger.debug(f"No trade for {symbol}: RSI {rsi} is neutral")
        except Exception as e:
            logger.error(f"Failed to process {symbol}: {type(e).__name__}: {str(e)}")
