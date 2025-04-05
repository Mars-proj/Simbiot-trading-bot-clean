from logging_setup import logger_main
import pandas as pd

class MarketRentgenCore:
    """Core market analysis module for deep insights."""
    def __init__(self):
        self.data = None
        logger_main.info("Initialized MarketRentgenCore")

    def load_data(self, ohlcv_data):
        """Loads OHLCV data for deep analysis."""
        try:
            self.data = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            self.data['timestamp'] = pd.to_datetime(self.data['timestamp'], unit='ms')
            logger_main.debug(f"Loaded {len(self.data)} data points for deep analysis")
        except Exception as e:
            logger_main.error(f"Error loading data: {e}")
            self.data = None

    def analyze_volume_spikes(self, threshold=2.0):
        """Detects volume spikes in the market data."""
        if self.data is None:
            logger_main.error("No data loaded for volume spike analysis")
            return None
        try:
            avg_volume = self.data['volume'].rolling(window=20).mean()
            volume_spike = self.data['volume'] / avg_volume
            spikes = volume_spike > threshold
            latest_spike = spikes.iloc[-1]
            logger_main.debug(f"Volume spike detected: {latest_spike}")
            return latest_spike
        except Exception as e:
            logger_main.error(f"Error analyzing volume spikes: {e}")
            return None

    def calculate_market_sentiment(self):
        """Calculates market sentiment based on price movements."""
        if self.data is None:
            logger_main.error("No data loaded for sentiment analysis")
            return None
        try:
            returns = self.data['close'].pct_change()
            positive_days = (returns > 0).sum()
            total_days = len(returns)
            sentiment = positive_days / total_days if total_days > 0 else 0
            logger_main.debug(f"Market sentiment: {sentiment}")
            return sentiment
        except Exception as e:
            logger_main.error(f"Error calculating market sentiment: {e}")
            return None
