import pandas as pd
import numpy as np
from logging_setup import logger_main, logger_exceptions
from trade_pool import global_trade_pool
from redis_client import redis_client
from monetization import monetization
from bot_user_data import get_user_deposit

class TradeAnalyzer:
    def __init__(self):
        self.min_trades_for_analysis = 10  # Minimum number of trades for analysis
        self.volatility_window = 10  # Window for volatility calculation
        self.cache_key_prefix = "trade_analyzer:stats:"
        logger_main.info("Initializing TradeAnalyzer")

    async def fetch_trades(self):
        """Fetches the latest trades"""
        logger_main.debug("Fetching the latest trades")
        trades = await global_trade_pool.get_all_trades()
        # Limit to 1000 trades
        trades = trades[-1000:] if len(trades) > 1000 else trades
        logger_main.debug(f"Fetched {len(trades)} trades")
        return trades

    def prepare_trades(self, trades):
        """Prepares trades for analysis"""
        logger_main.debug("Converting trades to DataFrame")
        try:
            df = pd.DataFrame(trades)
            if df.empty:
                logger_main.warning("Trade DataFrame is empty")
                return None
            # Convert timestamp to datetime
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                logger_main.debug(f"After timestamp conversion: {df['timestamp'].head()}")
                if df['timestamp'].isnull().all():
                    logger_main.warning("All timestamp values are invalid, skipping analysis")
                    return None
            else:
                logger_main.warning("Field 'timestamp' is missing in trade data, skipping analysis")
                return None
            logger_main.debug(f"Trades in DataFrame: {df.head().to_dict()}")
            return df
        except Exception as e:
            logger_main.error(f"Error preparing trades: {str(e)}")
            logger_exceptions.error(f"Error preparing trades: {str(e)}", exc_info=True)
            return None

    async def analyze_trade_success(self, user_id=None):
        """Analyzes trade success and market conditions"""
        logger_main.debug("Analyzing trade success")
        # Create a cache key based on user_id
        cache_key = f"{self.cache_key_prefix}{user_id if user_id else 'all'}"
        # Check Redis cache
        cached_analysis = await redis_client.get(cache_key)
        if cached_analysis:
            logger_main.debug(f"Using cached trade analysis for {user_id if user_id else 'all users'}")
            return cached_analysis
        try:
            trades = await self.fetch_trades()
            df = self.prepare_trades(trades)
            if df is None or len(df) < self.min_trades_for_analysis:
                logger_main.warning(f"Insufficient trades for analysis: {len(df) if df is not None else 0} trades, required {self.min_trades_for_analysis}")
                return {}
            # Filter by user_id if provided
            if user_id:
                df = df[df['user_id'] == user_id]
                if df.empty:
                    logger_main.warning(f"No trades found for user {user_id}")
                    return {}
            analysis = {}
            # General trade statistics
            total_trades = len(df)
            successful_trades = len(df[df['pnl'] > 0])
            success_rate = successful_trades / total_trades if total_trades > 0 else 0
            avg_pnl = df['pnl'].mean() if not df['pnl'].empty else 0
            analysis["total_trades"] = total_trades
            analysis["successful_trades"] = successful_trades
            analysis["success_rate"] = success_rate
            analysis["average_pnl"] = avg_pnl
            # Analysis by user (if user_id is not specified)
            if not user_id:
                user_stats = df.groupby('user_id').agg({
                    'pnl': ['mean', 'sum']
                }).to_dict()
                user_trade_counts = df['user_id'].value_counts().to_dict()
                # Получаем депозиты пользователей из bot_user_data
                user_deposits = {user: get_user_deposit(user) for user in user_trade_counts.keys()}
                analysis["user_stats"] = {
                    user: {
                        "avg_pnl": user_stats.get(('pnl', 'mean'), {}).get(user, 0),
                        "total_pnl": user_stats.get(('pnl', 'sum'), {}).get(user, 0),
                        "trade_count": user_trade_counts.get(user, 0),
                        "deposit": user_deposits.get(user, 0),
                        "commission": monetization.calculate_commission(user_deposits.get(user, 0), user_stats.get(('pnl', 'sum'), {}).get(user, 0))
                    }
                    for user in user_trade_counts.keys()
                }
            # Market conditions analysis
            market_conditions = df['market_conditions'].dropna()
            if not market_conditions.empty:
                market_df = pd.DataFrame(market_conditions.tolist())
                if 'avg_drop' in market_df and 'avg_volatility' in market_df:
                    avg_drop = market_df['avg_drop'].mean()
                    avg_volatility = market_df['avg_volatility'].mean()
                    analysis["market_conditions"] = {
                        "avg_drop": avg_drop,
                        "avg_volatility": avg_volatility
                    }
            # Cache the result in Redis for 10 minutes
            await redis_client.setex(cache_key, 600, analysis)
            logger_main.info(f"Trade analysis completed for {user_id if user_id else 'all users'}: {analysis}")
            return analysis
        except Exception as e:
            logger_main.error(f"Error analyzing trade success: {str(e)}")
            logger_exceptions.error(f"Error analyzing trade success: {str(e)}", exc_info=True)
            return {}

    def calculate_buy_sell_ratio(self, df):
        """Calculates the buy/sell ratio"""
        logger_main.debug("Calculating buy_sell_ratio")
        try:
            if 'side' not in df.columns:
                logger_main.warning("Field 'side' is missing in trade data, buy_sell_ratio not calculated")
                return 0
            buy_trades = len(df[df['side'] == 'buy'])
            sell_trades = len(df[df['side'] == 'sell'])
            total = buy_trades + sell_trades
            return buy_trades / total if total > 0 else 0
        except Exception as e:
            logger_main.error(f"Error calculating buy_sell_ratio: {str(e)}")
            logger_exceptions.error(f"Error calculating buy_sell_ratio: {str(e)}", exc_info=True)
            return 0

    def calculate_trade_volatility(self, df):
        """Calculates the average volatility of trades by symbols"""
        logger_main.debug("Calculating trade_volatility")
        try:
            if 'symbol' not in df.columns or 'price' not in df.columns:
                logger_main.warning("Fields 'symbol' or 'price' are missing in trade data, trade_volatility not calculated")
                return 0
            if len(df) < self.volatility_window:
                logger_main.warning(f"Insufficient trades for volatility calculation: {len(df)} trades, required {self.volatility_window}")
                return 0
            # Group by symbols
            volatility_by_symbol = {}
            for symbol in df['symbol'].unique():
                symbol_trades = df[df['symbol'] == symbol].sort_values(by='timestamp')
                if len(symbol_trades) >= self.volatility_window:
                    prices = symbol_trades['price'].tail(self.volatility_window)
                    returns = prices.pct_change().dropna()
                    if not returns.empty:
                        volatility = returns.std() * np.sqrt(252)  # Annualized volatility
                        volatility_by_symbol[symbol] = volatility
            # Average volatility across all symbols
            avg_volatility = np.mean(list(volatility_by_symbol.values())) if volatility_by_symbol else 0
            return avg_volatility
        except Exception as e:
            logger_main.error(f"Error calculating trade_volatility: {str(e)}")
            logger_exceptions.error(f"Error calculating trade_volatility: {str(e)}", exc_info=True)
            return 0

trade_analyzer = TradeAnalyzer()

__all__ = ['trade_analyzer']
