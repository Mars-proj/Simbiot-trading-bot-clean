import logging
import asyncio

logger = logging.getLogger("main")

async def analyze_market_state(exchange, timeframe='1h'):
    logger.info(f"Analyzing market state with timeframe {timeframe}")
    retry_count = 3
    for attempt in range(retry_count):
        try:
            logger.debug(f"Fetching ticker for BTC/USDT (attempt {attempt + 1}/{retry_count})")
            # Устанавливаем таймаут 10 секунд для запроса
            ticker = await asyncio.wait_for(
                exchange.fetch_ticker('BTC/USDT'),
                timeout=10
            )
            logger.debug(f"Ticker data: {ticker}")
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
        except asyncio.TimeoutError as te:
            logger.error(f"Timeout while fetching ticker on attempt {attempt + 1}/{retry_count}: {te}")
            if attempt < retry_count - 1:
                logger.info(f"Retrying in 5 seconds...")
                await asyncio.sleep(5)
            else:
                logger.error("Failed to fetch ticker after all retries due to timeout")
                return {'trend': 'neutral', 'volatility': 0.01}
        except Exception as e:
            logger.error(f"Failed to analyze market state on attempt {attempt + 1}/{retry_count}: {type(e).__name__}: {str(e)}")
            if attempt < retry_count - 1:
                logger.info(f"Retrying in 5 seconds...")
                await asyncio.sleep(5)
            else:
                logger.error("Failed to analyze market state after all retries")
                return {'trend': 'neutral', 'volatility': 0.01}
