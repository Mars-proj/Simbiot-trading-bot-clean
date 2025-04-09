# symbol_filter.py
import logging
import asyncio

logger = logging.getLogger("main")

async def filter_symbols(exchange, symbols, since, limit, timeframe, user=None, market_state=None, batch_size=500):
    """Фильтрует символы, оставляя только пары с USDT и достаточным объёмом торгов, по батчам."""
    try:
        valid_symbols = []
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            for symbol in batch:
                if not symbol.endswith('/USDT'):
                    continue
                try:
                    ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
                    if len(ohlcv) < limit:
                        logger.warning(f"Skipping {symbol}: insufficient data (only {len(ohlcv)} candles)")
                        continue
                    volume = sum(candle[5] for candle in ohlcv)
                    if volume == 0:
                        logger.warning(f"Skipping {symbol}: zero trading volume")
                        continue
                    valid_symbols.append(symbol)
                except Exception as e:
                    logger.error(f"Failed to fetch OHLCV for {symbol}: {type(e).__name__}: {str(e)}")
                    continue
                # Добавляем задержку 0.2 секунды между запросами
                await asyncio.sleep(0.2)
            logger.info(f"Processed batch {i//batch_size + 1} of {len(symbols)//batch_size + 1}, found {len(valid_symbols)} valid symbols so far")
        logger.info(f"Filtered {len(valid_symbols)} valid symbols for user {user or 'unknown'} in {market_state or 'unknown'} market state")
        return valid_symbols
    except Exception as e:
        logger.error(f"Failed to filter symbols: {type(e).__name__}: {str(e)}")
        return []
