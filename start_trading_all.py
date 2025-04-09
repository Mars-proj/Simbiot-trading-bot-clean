# start_trading_all.py
import logging
import time  # Добавляем импорт модуля time
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np

logger = logging.getLogger("main")

async def evaluate_trade(exchange, trade, symbol, user, market_state):
    try:
        # Получаем текущую цену
        ticker = await exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        
        # Получаем данные OHLCV для анализа
        ohlcv = await exchange.fetch_ohlcv(symbol, '1h', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Вычисляем RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # Логика оценки
        profit = (current_price - trade['price']) * trade['amount']
        holding_time = (time.time() * 1000 - trade['timestamp']) / (1000 * 60 * 60)  # Время в часах
        
        logger.debug(f"Evaluated trade for {symbol}: profit={profit:.2f}, RSI={current_rsi:.2f}, holding_time={holding_time:.2f} hours")
        
        # Простая логика закрытия позиции
        if current_rsi > 70 or profit > 0.05 * trade['cost'] or holding_time > 24:
            logger.info(f"Closing position for {symbol}: profit={profit:.2f}, RSI={current_rsi:.2f}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to evaluate trade for {symbol}: {type(e).__name__}: {str(e)}")
        return False

async def start_trading_all(exchange, symbols, user, market_state):
    signal_count = 0
    for symbol in symbols:
        try:
            # Проверяем баланс
            balance = await exchange.fetch_balance()
            usdt_balance = balance.get('USDT', {}).get('free', 0)
            if usdt_balance < 10:
                logger.warning(f"Insufficient USDT balance for {user}: {usdt_balance}")
                continue
            
            # Получаем данные OHLCV
            ohlcv = await exchange.fetch_ohlcv(symbol, '1h', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Простая торговая стратегия: покупаем, если цена выше 20-периодной SMA
            df['sma_20'] = df['close'].rolling(window=20).mean()
            current_price = df['close'].iloc[-1]
            sma_20 = df['sma_20'].iloc[-1]
            
            if current_price > sma_20:
                # Рассчитываем сумму ордера (10% от баланса, но не менее 10 USDT)
                amount_usd = max(10, usdt_balance * 0.1)
                amount = amount_usd / current_price
                
                # Создаём ордер
                trade = await exchange.create_market_buy_order(symbol, amount)
                logger.info(f"Buy trade executed for {symbol} on {exchange.id}: {trade}")
                logger.info(f"Order details: id={trade['id']}, status={trade['status']}, filled={trade['filled']}")
                
                # Оцениваем сделку
                should_close = await evaluate_trade(exchange, trade, symbol, user, market_state)
                if should_close:
                    # Закрываем позицию
                    await exchange.create_market_sell_order(symbol, amount)
                    logger.info(f"Sell trade executed for {symbol} on {exchange.id}")
                
                signal_count += 1
        except Exception as e:
            logger.error(f"Failed to process {symbol}: {type(e).__name__}: {str(e)}")
            continue
    return signal_count
