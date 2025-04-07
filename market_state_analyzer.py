import logging

logger = logging.getLogger("main")

async def analyze_market_state(exchange, timeframe='1h'):
    logger.info(f"Analyzing market state with timeframe {timeframe}")
    try:
        # Пример: Получаем данные тикера для BTC/USDT, чтобы определить состояние рынка
        ticker = await exchange.fetch_ticker('BTC/USDT')
        price_change = ticker['percentage']  # Процент изменения цены за 24 часа
        
        # Простой пример определения тренда
        trend = 'bullish' if price_change > 0 else 'bearish'
        
        # Пример: Оценка волатильности (можно улучшить с использованием OHLCV данных)
        volatility = abs(price_change) / 100  # Упрощённый расчёт

        market_state = {
            'trend': trend,
            'volatility': volatility,
        }
        logger.info(f"Market state analyzed: {market_state}")
        return market_state
    except Exception as e:
        logger.error(f"Failed to analyze market state: {e}")
        # Возвращаем значения по умолчанию в случае ошибки
        return {'trend': 'neutral', 'volatility': 0.01}
