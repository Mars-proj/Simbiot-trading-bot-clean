import pandas as pd
import numpy as np
from logging_setup import logger_main

def calculate_vwap(data):
    """Расчёт VWAP (Volume Weighted Average Price)"""
    try:
        # Проверка входных данных
        if not isinstance(data, pd.DataFrame):
            logger_main.error(f"Некорректный тип данных для VWAP: {type(data)}")
            return pd.Series()
        required_columns = ['high', 'low', 'close', 'volume']
        if not all(col in data.columns for col in required_columns):
            logger_main.error(f"Отсутствуют необходимые колонки для VWAP: {data.columns}")
            return pd.Series()
        if data.empty:
            logger_main.warning("Пустой DataFrame для VWAP")
            return pd.Series()
        # Рассчитываем типичную цену: (high + low + close) / 3
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        # Умножаем типичную цену на объём
        price_volume = typical_price * data['volume']
        # Кумулятивная сумма (цена * объём) / кумулятивный объём
        cumulative_price_volume = price_volume.cumsum()
        cumulative_volume = data['volume'].cumsum()
        vwap = cumulative_price_volume / cumulative_volume
        # Заполняем NaN нулями
        vwap = vwap.fillna(0)
        logger_main.debug(f"VWAP рассчитан, последнее значение: {vwap.iloc[-1] if not vwap.empty else 'пусто'}")
        return vwap
    except Exception as e:
        logger_main.error(f"Ошибка при расчёте VWAP: {str(e)}")
        return pd.Series()

__all__ = ['calculate_vwap']
