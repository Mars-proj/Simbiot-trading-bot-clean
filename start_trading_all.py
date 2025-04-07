import logging

logger = logging.getLogger("main")


async def start_trading_all(exchange, valid_symbols, user):
    logger.debug(f"Exchange instance received: {exchange.name}")
    logger.debug(f"Exchange methods available: {dir(exchange)}")
    for symbol in valid_symbols:
        try:
            amount = 5  # USDT
            logger.debug(f"Placing market buy order for {symbol} with amount {amount}")
            order = exchange.create_market_buy_order(symbol, amount)
            logger.info(f"Trade executed for {symbol} on {exchange.id}: {order}")
        except Exception as e:
            logger.error(f"Failed to execute trade for {symbol} on {exchange.id}: {e}")
