import ccxt.async_support as ccxt
import logging

logger = logging.getLogger(__name__)

class ExchangeDetector:
    def __init__(self):
        self.exchanges = {}

    async def detect_exchange(self, api_key, api_secret):
        logger.info("Detecting exchange for API key")
        for exchange_id in ccxt.exchanges:
            exchange = None
            try:
                exchange_class = getattr(ccxt, exchange_id)
                exchange = exchange_class({
                    'apiKey': api_key,
                    'secret': api_secret,
                    'enableRateLimit': True,
                })
                # Проверяем, поддерживает ли биржа асинхронные методы
                if not hasattr(exchange, 'fetch_tickers'):
                    logger.debug(f"Exchange {exchange_id} does not support fetch_tickers")
                    continue
                
                # Пробуем получить тикеры для проверки валидности API-ключей
                tickers = await exchange.fetch_tickers()
                if tickers:
                    self.exchanges[exchange_id] = exchange
                    logger.info(f"Detected exchange: {exchange_id}")
                    return exchange
                else:
                    logger.debug(f"Exchange {exchange_id} returned empty tickers")
                    await exchange.close()
            except Exception as e:
                logger.debug(f"Exchange {exchange_id} not matched: {str(e)}")
                if exchange:
                    try:
                        await exchange.close()
                        logger.debug(f"Closed connection for {exchange_id} after failure")
                    except Exception as close_err:
                        logger.error(f"Failed to close connection for {exchange_id}: {str(close_err)}")
                continue
        logger.error("No exchange detected for the provided API key")
        return None

    async def close(self):
        """
        Close all exchange connections.
        """
        for exchange_id, exchange in self.exchanges.items():
            try:
                await exchange.close()
                logger.info(f"Closed exchange connection for {exchange_id}")
            except Exception as e:
                logger.error(f"Failed to close exchange {exchange_id}: {str(e)}")
        self.exchanges.clear()
