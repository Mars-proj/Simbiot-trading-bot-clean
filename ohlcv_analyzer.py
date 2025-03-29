import pandas as pd
import pandas_ta as ta
from utils import logger_main, log_exception

class OHLCVAnalyzer:
    def __init__(self):
        pass

    def analyze(self, symbol, ohlcv):
        """Анализирует OHLCV-данные и возвращает рыночные условия"""
        logger_main.debug(f"Анализ OHLCV для {symbol}")
        try:
            if ohlcv is None or ohlcv.empty:
                logger_main.error(f"OHLCV-данные для {symbol} пусты")
                return {}

            # Вычисляем индикаторы
            ohlcv['sma_short'] = ohlcv['close'].rolling(window=20).mean()
            ohlcv['sma_long'] = ohlcv['close'].rolling(window=50).mean()
            ohlcv['returns'] = ohlcv['close'].pct_change()
            ohlcv['volatility'] = ohlcv['returns'].rolling(window=20).std()

            # Определяем тренд
            current_sma_short = ohlcv['sma_short'].iloc[-1]
            current_sma_long = ohlcv['sma_long'].iloc[-1]
            if current_sma_short > current_sma_long:
                trend = 'up'
            elif current_sma_short < current_sma_long:
                trend = 'down'
            else:
                trend = 'neutral'

            # Вычисляем волатильность
            volatility = ohlcv['volatility'].iloc[-1]

            return {
                symbol: {
                    'trend': trend,
                    'volatility': volatility if not pd.isna(volatility) else 0.0,
                    'sma_short': current_sma_short,
                    'sma_long': current_sma_long
                }
            }
        except Exception as e:
            logger_main.error(f"Ошибка при анализе OHLCV для {symbol}: {str(e)}")
            log_exception(f"Ошибка при анализе OHLCV: {str(e)}", e)
            return {}

__all__ = ['OHLCVAnalyzer']
