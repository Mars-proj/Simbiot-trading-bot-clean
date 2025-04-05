from logging_setup import logger_main
import pandas as pd

class MarketAnalyzer:
    """Analyzes market data for trading decisions."""
    def __init__(self):
        self.data = None
        logger_main.info("Initialized MarketAnalyzer")

    def load_data(self, ohlcv_data):
        """Loads OHLCV data for analysis."""
        try:
            self.data = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            self.data['timestamp'] = pd.to_datetime(self.data['timestamp'], unit='ms')
            logger_main.debug(f"Loaded {len(self.data)} data points for analysis")
        except Exception as e:
            logger_main.error(f"Error loading data: {e}")
            self.data = None

    def calculate_volatility(self, window=14):
        """Calculates volatility based on historical data."""
        if self.data is None:
            logger_main.error("No data loaded for volatility calculation")
            return None
        try:
            returns = self.data['close'].pct_change()
            volatility = returns.rolling(window=window).std() * (252 ** 0.5)  # Annualized volatility
            logger_main.debug(f"Calculated volatility with window {window}")
            return volatility.iloc[-1]
        except Exception as e:
            logger_main.error(f"Error calculating volatility: {e}")
            return None

    def detect_trend(self, window=20):
        """Detects the current market trend."""
        if self.data is None:
            logger_main.error("No data loaded for trend detection")
            return None
        try:
            self.data['sma'] = self.data['close'].rolling(window=window).mean()
            latest_price = self.data['close'].iloc[-1]
            latest_sma = self.data['sma'].iloc[-1]
            if latest_price > latest_sma:
                trend = 'up'
            elif latest_price < latest_sma:
                trend = 'down'
            else:
                trend = 'sideways'
            logger_main.debug(f"Detected trend: {trend}")
            return trend
        except Exception as e:
            logger_main.error(f"Error detecting trend: {e}")
            return None
