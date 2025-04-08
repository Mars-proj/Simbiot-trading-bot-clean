# Roadmap

## Completed Tasks
- [x] **Implement dynamic order amounts** (min $10, max flexible) - Completed in commit 37bc540 (2025-04-08)
- [x] **Add dynamic RSI thresholds** based on volatility and trade success - Completed in commit 37bc540 (2025-04-08)
- [x] **Add self-learning for RSI thresholds** using trade success data - Completed in commit 37bc540 (2025-04-08)
- [x] **Reduce cycle interval to 5 minutes** with adaptive adjustment - Completed in commit 0b904b8 (2025-04-08)
- [x] **Add performance monitoring and dynamic task management** for scalability - Completed in commit 0b904b8 (2025-04-08)
- [x] **Optimize API request handling** to avoid rate limits
  - Added delays between batches in `symbol_filter.py`.
  - Reduced `rateLimit` in `exchange_pool.py`.
  - Completed in commit 46a5222 (2025-04-07)
- [x] **Implement caching for historical data** in `historical_data_fetcher.py` - Completed in commit 7be087c (2025-04-06)
- [x] **Fix market fetching for spot markets** in `exchange_pool.py` - Completed in commit 7be087c (2025-04-06)

## In Progress
- [ ] **Implement market type detection** (trending, sideways, volatile) in `market_state_analyzer.py`
  - Use ADX for trend detection, Bollinger Bands for sideways markets, and ATR for volatility.
  - Status: Planned for next sprint.
- [ ] **Create `strategy_manager.py`** to select strategies based on market type
  - Define strategies: `rsi_sma_strategy` (trending), `bollinger_strategy` (sideways), `atr_cci_strategy` (volatile).
  - Status: Planned for next sprint.
- [ ] **Integrate strategy generation** using `learning/strategy_optimizer.py`
  - Combine indicators (RSI, MACD, Bollinger Bands, etc.) to create new strategies.
  - Backtest strategies using `learning/backtester.py`.
  - Status: Planned for next sprint.
- [ ] **Enhance self-learning** with `learning/trade_evaluator.py`
  - Track strategy success and adapt strategies (modify parameters, replace ineffective strategies).
  - Status: Planned for next sprint.

## Future Goals
- [ ] **Support multiple exchanges** (Binance, Bybit, etc.) in `exchange_pool.py`.
- [ ] **Implement distributed processing** using Celery for 1000+ users.
- [ ] **Implement advanced risk management** (dynamic stop-loss/take-profit based on ATR).
