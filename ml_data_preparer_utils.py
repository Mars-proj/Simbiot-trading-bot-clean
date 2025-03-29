import pandas as pd
import pandas_ta as ta
import asyncio
from utils import logger_main, log_exception

# Глобальный кэш для результатов бэктестинга (по биржам)
backtest_cache = {}

# Ограничение на количество одновременных запросов к API
MAX_CONCURRENT_REQUESTS = 5  # Ограничиваем до 5 параллельных запросов
REQUEST_DELAY = 0.5  # Задержка 0.5 секунды между запросами

# Создаём семафор для ограничения параллельных запросов
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

async def prepare_training_data(exchange, trades, timeframe='4h', limit=100):
    """Подготавливает данные для обучения на основе сделок из trade_pool"""
    logger_main.debug("Подготовка данных для обучения из trade_pool")
    try:
        # Создаём DataFrame из сделок
        trades_df = pd.DataFrame(trades)
        if trades_df.empty:
            logger_main.warning("Список сделок пуст")
            return None
        # Удаляем сделки с нулевым PNL
        trades_df = trades_df[trades_df['pnl'].notna() & (trades_df['pnl'] != 0)]
        if trades_df.empty:
            logger_main.warning("Нет сделок с ненулевым PNL для обучения")
            return None
        # Получаем OHLCV-данные для каждого символа
        data_list = []
        for _, trade in trades_df.iterrows():
            symbol = trade['symbol']
            timestamp = pd.to_datetime(trade['timestamp'])
            try:
                # Получаем OHLCV-данные за период до сделки
                async with semaphore:
                    ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                    await asyncio.sleep(REQUEST_DELAY)  # Задержка после каждого запроса
                ohlcv_df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                ohlcv_df['timestamp'] = pd.to_datetime(ohlcv_df['timestamp'], unit='ms')
                # Фильтруем данные до времени сделки
                ohlcv_df = ohlcv_df[ohlcv_df['timestamp'] <= timestamp]
                if ohlcv_df.empty:
                    logger_main.warning(f"Нет OHLCV-данных для {symbol} до времени сделки {timestamp}")
                    continue
                # Рассчитываем индикаторы
                ohlcv_df['rsi'] = ta.rsi(ohlcv_df['close'], length=14)
                macd = ta.macd(ohlcv_df['close'], fast=12, slow=26, signal=9)
                ohlcv_df['macd'] = macd['MACD_12_26_9']
                ohlcv_df['macd_signal'] = macd['MACDs_12_26_9']
                bb = ta.bbands(ohlcv_df['close'], length=20)
                ohlcv_df['bb_upper'] = bb['BBU_20_2.0']
                ohlcv_df['bb_middle'] = bb['BBM_20_2.0']
                ohlcv_df['bb_lower'] = bb['BBL_20_2.0']
                ohlcv_df['returns'] = ohlcv_df['close'].pct_change()
                ohlcv_df['volatility'] = ohlcv_df['returns'].rolling(window=20).std() * np.sqrt(252)
                # Добавляем данные о сделке
                trade_data = ohlcv_df.tail(1).copy()
                trade_data['amount'] = trade.get('amount', 0)
                trade_data['trade_success'] = 1 if trade['pnl'] > 0 else 0
                trade_data['future_close'] = ohlcv_df['close'].shift(-1).iloc[-1] if len(ohlcv_df) > 1 else trade_data['close'].iloc[0]
                data_list.append(trade_data)
            except Exception as e:
                logger_main.warning(f"Ошибка при обработке OHLCV для {symbol}: {str(e)}")
                continue
        if not data_list:
            logger_main.warning("Не удалось собрать данные для обучения из trade_pool")
            return None
        data = pd.concat(data_list, ignore_index=True)
        logger_main.debug(f"Собрано {len(data)} записей для обучения из trade_pool")
        return data
    except Exception as e:
        logger_main.error(f"Ошибка при подготовке данных из trade_pool: {str(e)}")
        log_exception(f"Ошибка при подготовке данных: {str(e)}", e)
        return None

__all__ = ['prepare_training_data', 'backtest_cache', 'MAX_CONCURRENT_REQUESTS', 'REQUEST_DELAY', 'semaphore']
