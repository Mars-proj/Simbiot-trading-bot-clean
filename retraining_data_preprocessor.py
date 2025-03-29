import numpy as np
from logging_setup import logger_main
from utils import log_exception
from momentum_indicators import calculate_rsi, calculate_stochastic_oscillator
from trend_indicators import calculate_macd, calculate_adx
from price_volatility_indicators import calculate_bollinger_bands, calculate_atr
from price_volume_indicators import calculate_vwap

class RetrainDataPreprocessor:
    def __init__(self):
        self.input_size = 22  # Expected number of features
        self.preprocessed_cache = {}  # Cache for preprocessed data

    def initialize_logging(self):
        """Initializes logging for RetrainDataPreprocessor"""
        logger_main.info("RetrainDataPreprocessor initialized")

    def preprocess_data(self, signal_data):
        """Preprocesses input data into a numerical vector with caching"""
        try:
            # Create a unique key for caching
            cache_key = str(signal_data)
            if cache_key in self.preprocessed_cache:
                logger_main.debug("Using cached preprocessed data")
                return self.preprocessed_cache[cache_key]
            signal_generator = signal_data.get('signals', {}).get('signal_generator', 0)
            strategy_signals = signal_data.get('signals', {}).get('strategy_signals', {})
            combined_signal = signal_data.get('signals', {}).get('combined_signal', 0)
            signal_metrics = signal_data.get('signal_metrics', {})
            market_conditions = signal_data.get('market_conditions', {})
            atr = signal_metrics.get('atr', 0)
            short_ma = signal_metrics.get('short_ma', 0)
            long_ma = signal_metrics.get('long_ma', 0)
            rsi = signal_metrics.get('rsi', 0)
            macd = signal_metrics.get('macd', 0)
            macd_signal = signal_metrics.get('macd_signal', 0)
            ma_short = signal_metrics.get('MovingAverageStrategy_ma_short', 0)
            ma_long = signal_metrics.get('MovingAverageStrategy_ma_long', 0)
            rsi_strategy = signal_metrics.get('RSIDivergenceStrategy_rsi', 0)
            bb_upper = signal_metrics.get('BollingerBandsBreakoutStrategy_bb_upper', 0)
            bb_middle = signal_metrics.get('BollingerBandsBreakoutStrategy_bb_middle', 0)
            bb_lower = signal_metrics.get('BollingerBandsBreakoutStrategy_bb_lower', 0)
            macd_strategy = signal_metrics.get('MACDTrendFollowingStrategy_macd', 0)
            macd_signal_strategy = signal_metrics.get('MACDTrendFollowingStrategy_macd_signal', 0)
            vwap = signal_metrics.get('VWAPStrategy_vwap', 0)
            stochastic_k = signal_metrics.get('StochasticStrategy_stochastic_k', 0)
            stochastic_d = signal_metrics.get('StochasticStrategy_stochastic_d', 0)
            adx = signal_metrics.get('ADXTrendStrategy_adx', 0)
            avg_drop = market_conditions.get('avg_drop', 0)
            avg_volatility = market_conditions.get('avg_volatility', 0)
            features = [
                signal_generator,
                combined_signal,
                strategy_signals.get('MovingAverageStrategy', 0),
                strategy_signals.get('RSIDivergenceStrategy', 0),
                strategy_signals.get('BollingerBandsBreakoutStrategy', 0),
                strategy_signals.get('MACDTrendFollowingStrategy', 0),
                atr,
                short_ma,
                long_ma,
                rsi,
                macd,
                macd_signal,
                ma_short,
                ma_long,
                rsi_strategy,
                bb_upper,
                bb_middle,
                bb_lower,
                macd_strategy,
                macd_signal_strategy,
                avg_drop,
                avg_volatility
            ]
            if len(features) != self.input_size:
                logger_main.error(f"Invalid input data size: expected {self.input_size}, got {len(features)}")
                return None
            features_array = np.array(features, dtype=np.float32)
            # Replace NaN and infinite values with column means
            if np.any(np.isnan(features_array)) or np.any(np.isinf(features_array)):
                logger_main.warning(f"Input data contains NaN or infinite values: {features}")
                mean_value = np.nanmean(features_array)
                features_array = np.where(np.isnan(features_array) | np.isinf(features_array), mean_value, features_array)
                logger_main.debug(f"NaN and infinite values replaced with mean: {mean_value}")
            self.preprocessed_cache[cache_key] = features_array
            return features_array
        except Exception as e:
            log_exception("Error preprocessing data", e)
            return None

    def preprocess_trades(self, trades):
        """Preprocesses trades into training data"""
        X, y = [], []
        successful_trades = 0
        failed_trades = 0
        for trade in trades:
            signal_data = {
                'signals': trade.get('signals', {}),
                'signal_metrics': trade.get('signal_metrics', {}),
                'market_conditions': trade.get('market_conditions', {})
            }
            features = self.preprocess_data(signal_data)
            if features is None:
                continue
            status = trade.get('status', 'pending')
            if status == 'successful':
                label = 1.0
                successful_trades += 1
            elif status == 'failed':
                label = 0.0
                failed_trades += 1
            else:
                continue
            X.append(features)
            y.append(label)
        if not X or not y:
            logger_main.warning("No data for retraining after filtering")
            return None, None
        logger_main.info(f"Label distribution: successful trades: {successful_trades}, failed trades: {failed_trades}")
        return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

__all__ = ['RetrainDataPreprocessor']
