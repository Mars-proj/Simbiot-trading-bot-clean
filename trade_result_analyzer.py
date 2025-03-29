import asyncio
from logging_setup import logger_main
from utils import log_exception
from data_fetcher import fetch_ticker_cached
from redis_client import redis_client

class TradeResultAnalyzer:
    def __init__(self, trade_pool, retrain_engine):
        self.trade_pool = trade_pool
        self.retrain_engine = retrain_engine
        self.success_threshold = 0.02  # Success threshold: 2% price increase/decrease
        self.wait_time = 4 * 3600  # Wait 4 hours to determine the result
        self.min_trades_for_retraining = 10  # Minimum trades for retraining
        logger_main.info("Initializing TradeResultAnalyzer")

    async def analyze_trades(self, exchange):
        """Analyzes trades from the pool, determines their results, and retrains RetrainEngine"""
        try:
            logger_main.info("Starting trade result analysis")
            trades = await self.trade_pool.get_all_trades()
            logger_main.debug(f"Retrieved {len(trades)} trades from the pool")
            # Analyze each trade
            for trade_data in trades:
                if trade_data['status'] != 'filled' or 'success_label' in trade_data:
                    continue
                symbol = trade_data['symbol']
                timestamp = trade_data['timestamp']
                side = trade_data['side']
                original_price = trade_data['price']
                amount = trade_data['amount']
                trade_id = trade_data['trade_id']
                # Wait 4 hours after the trade
                elapsed_time = (asyncio.get_event_loop().time() * 1000 - timestamp) / 1000  # Time in seconds
                if elapsed_time < self.wait_time:
                    logger_main.debug(f"Trade {trade_id} is not ready for analysis, waiting {self.wait_time - elapsed_time} seconds")
                    continue
                # Fetch current price
                ticker = await fetch_ticker_cached(exchange, symbol)
                if not ticker or 'last' not in ticker:
                    logger_main.error(f"Failed to fetch current price for {symbol}, skipping trade {trade_id}")
                    continue
                current_price = ticker['last']
                logger_main.debug(f"Current price for {symbol}: {current_price}, original price: {original_price}")
                # Determine trade result
                if side == 'buy':
                    success = current_price > original_price * (1 + self.success_threshold)  # Price increased by 2%
                else:
                    success = current_price < original_price * (1 - self.success_threshold)  # Price decreased by 2%
                trade_data['success_label'] = 1 if success else 0
                trade_data['pnl'] = (current_price - original_price) * amount if side == 'buy' else (original_price - current_price) * amount
                await self.trade_pool.update_trade(trade_id, trade_data)
                logger_main.info(f"Updated trade {trade_id}: success_label={trade_data['success_label']}, pnl={trade_data['pnl']}")
            # Prepare dataset for retraining
            training_data = []
            for trade_data in trades:
                if 'success_label' not in trade_data:
                    continue
                sample = {
                    'signals': trade_data['signals'],
                    'signal_metrics': trade_data['signal_metrics'],
                    'market_conditions': trade_data['market_conditions'],
                    'status': 'successful' if trade_data['success_label'] == 1 else 'failed',
                    'pnl': trade_data['pnl']
                }
                training_data.append(sample)
            logger_main.debug(f"Prepared training dataset: {len(training_data)} samples")
            # Retrain RetrainEngine
            if len(training_data) >= self.min_trades_for_retraining:
                await self.retrain_engine.retrain(training_data)
                logger_main.info("RetrainEngine retrained based on trade pool")
            else:
                logger_main.warning(f"Insufficient data for retraining: {len(training_data)} samples, required minimum {self.min_trades_for_retraining}")
        except Exception as e:
            logger_main.error(f"Error analyzing trades: {str(e)}")
            log_exception(f"Error analyzing trades: {str(e)}", e)

__all__ = ['TradeResultAnalyzer']
