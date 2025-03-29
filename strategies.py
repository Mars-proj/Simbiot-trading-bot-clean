import numpy as np
from logging_setup import logger_main

class MovingAverageStrategy:
    def __init__(self):
        self.short_period = None
        self.long_period = None

    def _calculate_dynamic_periods(self, ohlcv_data):
        """Динамически определяет периоды скользящих средних на основе волатильности"""
        try:
            closes = [candle[4] for candle in ohlcv_data[-50:]]
            if len(closes) < 50:
                return 10, 20  # Значения по умолчанию
            returns = np.diff(closes) / closes[:-1]
            volatility = np.std(returns)
            # Чем выше волатильность, тем короче периоды
            self.short_period = max(5, int(15 * (1 - volatility)))
            self.long_period = max(10, int(30 * (1 - volatility)))
            logger_main.debug(f"Dynamic MA periods: short={self.short_period}, long={self.long_period}, volatility={volatility}")
            return self.short_period, self.long_period
        except Exception as e:
            logger_main.warning(f"Error calculating dynamic periods: {str(e)}")
            return 10, 20

    def _calculate_ema(self, data, period):
        """Рассчитывает экспоненциальную скользящую среднюю"""
        alpha = 2 / (period + 1)
        ema = [data[0]]
        for price in data[1:]:
            ema.append(alpha * price + (1 - alpha) * ema[-1])
        return ema[-1]

    def generate_signal(self, ohlcv_data):
        """Генерация сигнала на основе скользящих средних"""
        try:
            if not ohlcv_data or len(ohlcv_data) < 50:
                logger_main.warning("Недостаточно данных для MovingAverageStrategy")
                return 0
            short_period, long_period = self._calculate_dynamic_periods(ohlcv_data)
            closes = [candle[4] for candle in ohlcv_data]
            short_ema = self._calculate_ema(closes[-short_period:], short_period)
            long_ema = self._calculate_ema(closes[-long_period:], long_period)
            if short_ema > long_ema:
                return 1  # Buy
            elif short_ema < long_ema:
                return -1  # Sell
            return 0  # Neutral
        except Exception as e:
            logger_main.error(f"Ошибка в MovingAverageStrategy: {str(e)}")
            return 0

class RSIDivergenceStrategy:
    def __init__(self):
        self.rsi_period = None
        self.overbought = None
        self.oversold = None

    def _calculate_dynamic_rsi_params(self, ohlcv_data):
        """Динамически определяет параметры RSI на основе волатильности"""
        try:
            closes = [candle[4] for candle in ohlcv_data[-50:]]
            if len(closes) < 50:
                return 14, 70, 30  # Значения по умолчанию
            returns = np.diff(closes) / closes[:-1]
            volatility = np.std(returns)
            # Чем выше волатильность, тем короче период и шире пороги
            self.rsi_period = max(10, int(20 * (1 - volatility)))
            self.overbought = min(80, 70 + 10 * volatility)
            self.oversold = max(20, 30 - 10 * volatility)
            logger_main.debug(f"Dynamic RSI params: period={self.rsi_period}, overbought={self.overbought}, oversold={self.oversold}, volatility={volatility}")
            return self.rsi_period, self.overbought, self.oversold
        except Exception as e:
            logger_main.warning(f"Error calculating dynamic RSI params: {str(e)}")
            return 14, 70, 30

    def generate_signal(self, ohlcv_data):
        """Генерация сигнала на основе RSI"""
        try:
            if not ohlcv_data or len(ohlcv_data) < 50:
                logger_main.warning("Недостаточно данных для RSIDivergenceStrategy")
                return 0
            rsi_period, overbought, oversold = self._calculate_dynamic_rsi_params(ohlcv_data)
            closes = [candle[4] for candle in ohlcv_data[-rsi_period:]]
            delta = np.diff(closes)
            gain = np.mean([d for d in delta if d > 0]) if any(d > 0 for d in delta) else 0
            loss = -np.mean([d for d in delta if d < 0]) if any(d < 0 for d in delta) else 0
            rs = gain / loss if loss != 0 else 0
            rsi = 100 - (100 / (1 + rs)) if rs != 0 else 0
            if rsi < oversold:
                return 1  # Buy
            elif rsi > overbought:
                return -1  # Sell
            return 0  # Neutral
        except Exception as e:
            logger_main.error(f"Ошибка в RSIDivergenceStrategy: {str(e)}")
            return 0

class BollingerBandsBreakoutStrategy:
    def __init__(self):
        self.bb_period = None
        self.std_dev = None

    def _calculate_dynamic_bb_params(self, ohlcv_data):
        """Динамически определяет параметры Bollinger Bands на основе волатильности"""
        try:
            closes = [candle[4] for candle in ohlcv_data[-50:]]
            if len(closes) < 50:
                return 20, 2  # Значения по умолчанию
            returns = np.diff(closes) / closes[:-1]
            volatility = np.std(returns)
            # Чем выше волатильность, тем короче период и больше отклонение
            self.bb_period = max(10, int(30 * (1 - volatility)))
            self.std_dev = 2 + volatility  # Увеличиваем отклонение при высокой волатильности
            logger_main.debug(f"Dynamic BB params: period={self.bb_period}, std_dev={self.std_dev}, volatility={volatility}")
            return self.bb_period, self.std_dev
        except Exception as e:
            logger_main.warning(f"Error calculating dynamic BB params: {str(e)}")
            return 20, 2

    def generate_signal(self, ohlcv_data):
        """Генерация сигнала на основе Bollinger Bands"""
        try:
            if not ohlcv_data or len(ohlcv_data) < 50:
                logger_main.warning("Недостаточно данных для BollingerBandsBreakoutStrategy")
                return 0
            bb_period, std_dev = self._calculate_dynamic_bb_params(ohlcv_data)
            closes = [candle[4] for candle in ohlcv_data[-bb_period:]]
            sma = np.mean(closes)
            std = np.std(closes)
            upper_band = sma + std_dev * std
            lower_band = sma - std_dev * std
            last_close = closes[-1]
            if last_close > upper_band:
                return -1  # Sell
            elif last_close < lower_band:
                return 1  # Buy
            return 0  # Neutral
        except Exception as e:
            logger_main.error(f"Ошибка в BollingerBandsBreakoutStrategy: {str(e)}")
            return 0

class MACDTrendFollowingStrategy:
    def __init__(self):
        self.fast_period = None
        self.slow_period = None
        self.signal_period = None

    def _calculate_dynamic_macd_params(self, ohlcv_data):
        """Динамически определяет параметры MACD на основе волатильности"""
        try:
            closes = [candle[4] for candle in ohlcv_data[-50:]]
            if len(closes) < 50:
                return 12, 26, 9  # Значения по умолчанию
            returns = np.diff(closes) / closes[:-1]
            volatility = np.std(returns)
            # Чем выше волатильность, тем короче периоды
            self.fast_period = max(8, int(15 * (1 - volatility)))
            self.slow_period = max(20, int(30 * (1 - volatility)))
            self.signal_period = max(5, int(10 * (1 - volatility)))
            logger_main.debug(f"Dynamic MACD params: fast={self.fast_period}, slow={self.slow_period}, signal={self.signal_period}, volatility={volatility}")
            return self.fast_period, self.slow_period, self.signal_period
        except Exception as e:
            logger_main.warning(f"Error calculating dynamic MACD params: {str(e)}")
            return 12, 26, 9

    def _calculate_ema(self, data, period):
        """Рассчитывает экспоненциальную скользящую среднюю"""
        alpha = 2 / (period + 1)
        ema = [data[0]]
        for price in data[1:]:
            ema.append(alpha * price + (1 - alpha) * ema[-1])
        return ema

    def generate_signal(self, ohlcv_data):
        """Генерация сигнала на основе MACD"""
        try:
            if not ohlcv_data or len(ohlcv_data) < 50:
                logger_main.warning("Недостаточно данных для MACDTrendFollowingStrategy")
                return 0
            fast_period, slow_period, signal_period = self._calculate_dynamic_macd_params(ohlcv_data)
            closes = [candle[4] for candle in ohlcv_data]
            ema_fast = self._calculate_ema(closes[-fast_period:], fast_period)[-1]
            ema_slow = self._calculate_ema(closes[-slow_period:], slow_period)[-1]
            macd = ema_fast - ema_slow
            macd_values = [self._calculate_ema(closes[i-fast_period:i], fast_period)[-1] - self._calculate_ema(closes[i-slow_period:i], slow_period)[-1] for i in range(-signal_period, 0)]
            signal_line = np.mean(macd_values)
            if macd > signal_line:
                return 1  # Buy
            elif macd < signal_line:
                return -1  # Sell
            return 0  # Neutral
        except Exception as e:
            logger_main.error(f"Ошибка в MACDTrendFollowingStrategy: {str(e)}")
            return 0

__all__ = ['MovingAverageStrategy', 'RSIDivergenceStrategy', 'BollingerBandsBreakoutStrategy', 'MACDTrendFollowingStrategy']
