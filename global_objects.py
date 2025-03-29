# Global objects for the trading system
from trade_pool_core import TradePool
from redis_initializer import redis_client

# Global trade pool instance
global_trade_pool = TradePool()

__all__ = ['global_trade_pool', 'redis_client']
