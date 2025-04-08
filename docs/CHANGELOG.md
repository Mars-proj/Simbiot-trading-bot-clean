# Changelog

## [2025-04-08] - Commit 0b904b8
- **Enhancement**: Reduced cycle interval from 1 hour to 5 minutes in `core.py` to capture more trading signals.
- **Enhancement**: Added adaptive cycle interval in `core.py`, adjusting between 1 and 10 minutes based on signal frequency.
- **Enhancement**: Added performance monitoring and dynamic task management in `core.py` to improve scalability for 1000+ users.
- **Enhancement**: Added signal count return in `start_trading_all.py` to support adaptive cycle intervals.

## [2025-04-08] - Commit 37bc540
- **Enhancement**: Added dynamic order amounts in `start_trading_all.py` (minimum $10, maximum flexible based on liquidity and volatility).
- **Enhancement**: Implemented dynamic RSI thresholds in `start_trading_all.py`, adjusted based on volatility and trade success.
- **Enhancement**: Added self-learning mechanism in `start_trading_all.py` to track trade success and adapt RSI thresholds.

## [2025-04-07] - Commit 46a5222
- **Optimization**: Added 1-second delay between batches in `symbol_filter.py` to avoid API rate limits.
- **Optimization**: Reduced `rateLimit` to 100ms in `exchange_pool.py` to speed up API requests.

## [2025-04-06] - Commit 7be087c
- **Feature**: Added caching in Redis for historical data in `historical_data_fetcher.py`.
- **Fix**: Fixed market fetching in `exchange_pool.py` for spot markets.

## [Previous Entries]
...
