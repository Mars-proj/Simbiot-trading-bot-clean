import pandas as pd
from utils import logger_main, log_exception
import time

# Переменная для отслеживания времени последней паузы
last_market_pause = 0
PAUSE_DURATION = 3600  # 1 час паузы в секундах
MARKET_DROP_THRESHOLD = 0.05  # Порог падения рынка (5%)
VOLATILITY_THRESHOLD = 0.03  # Порог волатильности (3%)
suspended_users = {}  # Пользователи, для которых торговля приостановлена из-за зависаний
suspension_duration = 300  # Приостановка на 5 минут

async def check_market_trend(exchange, user_id):
    """Проверка общего тренда рынка через анализ цен BTC/USDT и ETH/USDT (асинхронный вызов)"""
    try:
        global last_market_pause, suspended_users
        current_time = time.time()
        # Проверяем, не приостановлена ли торговля для пользователя
        if user_id in suspended_users:
            suspension_end = suspended_users[user_id]
            if current_time < suspension_end:
                logger_main.warning(f"Торговля для пользователя {user_id} приостановлена до {suspension_end} из-за проблем с API, пропускаем")
                return False, None
            else:
                logger_main.info(f"Возобновляем торговлю для пользователя {user_id}")
                del suspended_users[user_id]
        # Проверяем, не находимся ли мы в режиме паузы
        if current_time < last_market_pause + PAUSE_DURATION:
            remaining_time = int(last_market_pause + PAUSE_DURATION - current_time)
            logger_main.warning(f"Торговля приостановлена из-за падения рынка или высокой волатильности, осталось {remaining_time} секунд")
            return False, None
        # Символы для проверки тренда
        trend_symbols = ['BTC/USDT', 'ETH/USDT']
        total_drop = 0
        total_volatility = 0
        timeframe = '4h'
        limit = 2  # Последние 2 свечи (текущая и предыдущая)
        for symbol in trend_symbols:
            try:
                logger_main.debug(f"Проверка тренда и волатильности для {symbol}")
                # Используем асинхронный вызов fetch_ohlcv
                ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                if len(df) < 2:
                    logger_main.warning(f"Недостаточно данных для {symbol}, пропускаем")
                    continue
                # Вычисляем процентное изменение цены
                previous_close = df.iloc[-2]['close']
                current_close = df.iloc[-1]['close']
                drop = (previous_close - current_close) / previous_close
                total_drop += drop
                logger_main.debug(f"Падение {symbol}: {drop:.2%}")
                # Вычисляем волатильность (диапазон high-low в процентах от close)
                high = df.iloc[-1]['high']
                low = df.iloc[-1]['low']
                volatility = (high - low) / current_close
                total_volatility += volatility
                logger_main.debug(f"Волатильность {symbol}: {volatility:.2%}")
            except Exception as e:
                logger_main.error(f"Ошибка при проверке тренда для {symbol} для пользователя {user_id}: {str(e)}")
                log_exception(f"Ошибка при проверке тренда для {symbol}: {str(e)}", e)
                logger_main.error(f"Приостанавливаем торговлю для пользователя {user_id} на {suspension_duration} секунд")
                suspended_users[user_id] = current_time + suspension_duration
                return False, None
        # Среднее падение и волатильность по символам
        avg_drop = total_drop / len(trend_symbols) if trend_symbols else 0
        avg_volatility = total_volatility / len(trend_symbols) if trend_symbols else 0
        logger_main.debug(f"Среднее падение рынка: {avg_drop:.2%}, средняя волатильность: {avg_volatility:.2%}")
        if avg_drop > MARKET_DROP_THRESHOLD:
            logger_main.error(f"Рынок упал более чем на {MARKET_DROP_THRESHOLD*100}% ({avg_drop:.2%}), приостанавливаем торговлю на {PAUSE_DURATION/3600} часов")
            last_market_pause = current_time
            return False, None
        if avg_volatility > VOLATILITY_THRESHOLD:
            logger_main.error(f"Волатильность рынка превышает {VOLATILITY_THRESHOLD*100}% ({avg_volatility:.2%}), приостанавливаем торговлю на {PAUSE_DURATION/3600} часов")
            last_market_pause = current_time
            return False, None
        market_conditions = {
            'avg_drop': avg_drop,
            'avg_volatility': avg_volatility
        }
        return True, market_conditions
    except Exception as e:
        logger_main.error(f"Ошибка при проверке тренда рынка для пользователя {user_id}: {str(e)}")
        log_exception(f"Ошибка при проверке тренда рынка: {str(e)}", e)
        logger_main.error(f"Приостанавливаем торговлю для пользователя {user_id} на {suspension_duration} секунд")
        suspended_users[user_id] = current_time + suspension_duration
        return False, None

__all__ = ['check_market_trend']
