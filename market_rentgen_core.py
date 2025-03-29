import pandas as pd
import numpy as np
import pandas_ta as ta
from logging_setup import logger_main
from utils import log_exception
from global_objects import global_trade_pool
from ml_predictor import ml_predictor, initialize_ml_predictor
from ml_data_preparer import MLDataPreparer
from strategy_recommender import StrategyRecommender
from retraining_engine import RetrainEngine

class MarketRentgen:
    def __init__(self):
        self.data_preparer = MLDataPreparer()
        self.strategy_recommender = StrategyRecommender()
        self._ml_predictor = ml_predictor

    async def initialize(self, exchange):
        """Initializes MarketRentgen"""
        logger_main.info("Initializing MarketRentgen")
        # Initialize ml_predictor logging
        initialize_ml_predictor()
        # Check and initialize ml_predictor if it is None
        global ml_predictor
        if self._ml_predictor is None:
            logger_main.warning("ml_predictor is not initialized, creating a new instance")
            self._ml_predictor = RetrainEngine()
            ml_predictor = self._ml_predictor
        # Train the ML model from ml_predictor
        await self._ml_predictor.retrain()

    async def analyze_ohlcv(self, symbol, df):
        """Analyzes OHLCV data"""
        logger_main.info(f"Analyzing OHLCV for {symbol}")
        try:
            analysis = {symbol: {}}
            # Determine the trend
            df['sma_short'] = df['close'].rolling(window=20).mean()
            df['sma_long'] = df['close'].rolling(window=50).mean()
            trend = 'up' if df['sma_short'].iloc[-1] > df['sma_long'].iloc[-1] else 'down'
            analysis[symbol]['trend'] = trend
            # Calculate volatility
            df['returns'] = df['close'].pct_change()
            if df['returns'].isna().all() or len(df['returns'].dropna()) < 20:
                logger_main.warning(f"Insufficient data or NaN in returns for volatility calculation for {symbol}")
                volatility = 0.01
            else:
                volatility = df['returns'].rolling(window=20).std().iloc[-1] * np.sqrt(252)
                volatility = volatility if not np.isnan(volatility) else 0.01
                volatility = max(volatility, 0.01)
            logger_main.info(f"Calculated volatility for {symbol}: {volatility:.4f}")
            analysis[symbol]['volatility'] = volatility
            analysis[symbol]['sma_short'] = df['sma_short'].iloc[-1]
            analysis[symbol]['sma_long'] = df['sma_long'].iloc[-1]
            # Add Bollinger Bands
            bb = ta.bbands(df['close'], length=20)
            analysis[symbol]['bb_upper'] = bb['BBU_20_2.0'].iloc[-1] if not bb['BBU_20_2.0'].isna().all() else 0
            analysis[symbol]['bb_middle'] = bb['BBM_20_2.0'].iloc[-1] if not bb['BBM_20_2.0'].isna().all() else 0
            analysis[symbol]['bb_lower'] = bb['BBL_20_2.0'].iloc[-1] if not bb['BBL_20_2.0'].isna().all() else 0
            # Determine if the market is sideways
            sma_diff = abs(df['sma_short'].iloc[-1] - df['sma_long'].iloc[-1]) / df['sma_long'].iloc[-1]
            is_sideways = sma_diff < 0.02
            analysis[symbol]['is_sideways'] = is_sideways
            logger_main.info(f"OHLCV analysis for {symbol}: {analysis[symbol]}")
            return analysis
        except Exception as e:
            logger_main.error(f"Error analyzing OHLCV for {symbol}: {str(e)}")
            log_exception(f"Error analyzing OHLCV: {str(e)}", e)
            return {symbol: {'trend': 'neutral', 'volatility': 0.01, 'sma_short': 0, 'sma_long': 0, 'bb_upper': 0, 'bb_middle': 0, 'bb_lower': 0, 'is_sideways': False}}

    def analyze_trades(self, trades):
        """Analyzes the success of trades"""
        logger_main.info("Analyzing trades")
        try:
            total_trades = len(trades)
            successful_trades = sum(1 for trade in trades if trade.get('pnl', 0) > 0)
            average_pnl = sum(trade.get('pnl', 0) for trade in trades) / total_trades if total_trades > 0 else 0
            # Analyze by strategy
            strategy_performance = {}
            for trade in trades:
                strategy = trade.get('strategy', 'unknown')
                if strategy not in strategy_performance:
                    strategy_performance[strategy] = []
                strategy_performance[strategy].append(trade.get('pnl', 0))
            # Calculate average success rate by strategy
            for strategy in strategy_performance:
                pnls = strategy_performance[strategy]
                strategy_performance[strategy] = sum(1 for pnl in pnls if pnl > 0) / len(pnls) if pnls else 0
            best_strategy = max(strategy_performance, key=strategy_performance.get, default='unknown')
            analysis = {
                'total_trades': total_trades,
                'successful_trades': successful_trades,
                'average_pnl': average_pnl,
                'strategy_performance': strategy_performance,
                'best_strategy': best_strategy
            }
            logger_main.info(f"Trade analysis: {analysis}")
            return analysis
        except Exception as e:
            logger_main.error(f"Error analyzing trade success: {str(e)}")
            log_exception(f"Error analyzing trades: {str(e)}", e)
            return {
                'total_trades': 0,
                'successful_trades': 0,
                'average_pnl': 0,
                'strategy_performance': {},
                'best_strategy': 'unknown'
            }

    def predict_success(self, symbol, df, trades):
        """Predicts the success probability of a trade using ml_predictor"""
        logger_main.info(f"Predicting success probability for {symbol}")
        try:
            if self._ml_predictor is None:
                logger_main.error(f"ml_predictor is not initialized for {symbol}")
                return None
            # Prepare signal_data for prediction
            signal_data = {
                'symbol': symbol,
                'signals': {
                    'signal_generator': 0,  # Placeholder, can be updated based on actual signal generation
                    'strategy_signals': {},
                    'combined_signal': 0
                },
                'signal_metrics': {
                    'atr': df['close'].pct_change().rolling(window=14).std().iloc[-1] if len(df) >= 14 else 0,
                    'short_ma': df['close'].rolling(window=20).mean().iloc[-1] if len(df) >= 20 else 0,
                    'long_ma': df['close'].rolling(window=50).mean().iloc[-1] if len(df) >= 50 else 0,
                    'rsi': ta.rsi(df['close'], length=14).iloc[-1] if len(df) >= 14 else 0,
                    'macd': ta.macd(df['close'])['MACD_12_26_9'].iloc[-1] if len(df) >= 26 else 0,
                    'macd_signal': ta.macd(df['close'])['MACDs_12_26_9'].iloc[-1] if len(df) >= 26 else 0,
                },
                'market_conditions': {
                    'avg_drop': df['close'].pct_change().mean() if not df['close'].empty else 0,
                    'avg_volatility': df['close'].pct_change().std() * np.sqrt(252) if not df['close'].empty else 0.01
                }
            }
            success_prob = self._ml_predictor.predict(signal_data)
            logger_main.info(f"Predicted success probability for {symbol}: {success_prob if success_prob is not None else 'undefined'}")
            return success_prob
        except Exception as e:
            logger_main.error(f"Error predicting success probability for {symbol}: {str(e)}")
            log_exception(f"Error predicting success: {str(e)}", e)
            return None

    async def get_strategy_recommendation(self, symbol, df, trades):
        """Recommends a strategy based on analysis and StrategyRecommender"""
        logger_main.info("Generating strategy recommendations with ML")
        try:
            # Analyze OHLCV
            ohlcv_analysis = await self.analyze_ohlcv(symbol, df)
            market_conditions = ohlcv_analysis[symbol]
            # Predict success probability
            success_prob = self.predict_success(symbol, df, trades)
            # Analyze trade success
            trade_analysis = self.analyze_trades(trades)
            # Get recommendation from StrategyRecommender
            recommendation = await self.strategy_recommender.recommend_strategy(df, success_prob)
            logger_main.info(f"Recommendation from StrategyRecommender for {symbol}: {recommendation}")
            return {
                'strategy_name': recommendation['strategy_name'],
                'rsi_buy': recommendation['rsi_buy'],
                'rsi_sell': recommendation['rsi_sell'],
                'stop_loss_percentage': recommendation['stop_loss_percentage'],
                'take_profit_drop': recommendation['take_profit_drop'],
                'sma_short_window': recommendation['sma_short_window'],
                'sma_long_window': recommendation['sma_long_window'],
                'volatility_threshold': recommendation['volatility_threshold'],
                'success_prob': success_prob,
                'market_conditions': market_conditions
            }
        except Exception as e:
            logger_main.error(f"Error generating recommendations for {symbol}: {str(e)}")
            log_exception(f"Error generating recommendations: {str(e)}", e)
            return {
                'strategy_name': 'trend',
                'rsi_buy': 30.0,
                'rsi_sell': 70.0,
                'stop_loss_percentage': 0.03,
                'take_profit_drop': 0.04,
                'sma_short_window': 10,
                'sma_long_window': 30,
                'volatility_threshold': 0.1,
                'success_prob': None,
                'market_conditions': {'trend': 'neutral', 'volatility': 0.01, 'sma_short': 0, 'sma_long': 0, 'bb_upper': 0, 'bb_middle': 0, 'bb_lower': 0, 'is_sideways': False}
            }

# Create a global instance of MarketRentgen
market_rentgen = MarketRentgen()

__all__ = ['market_rentgen']
