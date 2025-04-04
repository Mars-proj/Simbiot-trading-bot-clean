# Trading Bot Roadmap

## Overview
This roadmap outlines the development plan for the Trading Bot system, a self-learning, self-evolving market X-ray system designed to scale for 1000+ users. The project is being developed by the Symbiotes team.

## Current Status (as of April 3, 2025)
- **Core System**: The system is operational with basic trading functionality on MEXC (real keys, non-testnet).
- **Backtesting**: Implemented backtesting for all symbols with caching in `backtest_results.json`.
- **Symbol Filtering**: Filtering symbols based on backtest results, but currently stuck on `TGTUSDT` due to an unknown issue.
- **Model Retraining**: Retraining pipeline implemented, but currently failing due to issues with `trade_data` being empty.
- **Recent Fixes**:
  - Fixed `fetch_historical_data` to fetch 90 days of data for `BTCUSDT`, resolving the issue with insufficient data points for RSI (41 data points now available).
  - Fixed `ml_data_preparer.py` to handle empty `trade_data` by using an alternative method for target variable `y`.
  - Updated `collect_training_data` to fetch recent trades via `fetch_my_trades`, but still returning empty due to lack of trades for the user.

## Milestones

### Milestone 1: Core Functionality (In Progress)
- [x] Set up basic trading system with MEXC integration.
- [x] Implement backtesting for all symbols.
- [x] Cache backtest results in `backtest_results.json`.
- [x] Filter symbols based on backtest profit threshold.
- [ ] Fix symbol filtering issue (currently stuck on `TGTUSDT`).
- [ ] Resolve `trade_data` issue in `collect_training_data` to enable model retraining.
- [ ] Start trading for `user1` with filtered symbols.

### Milestone 2: Self-Learning and Self-Evolving
- [ ] Integrate LSTM and RL models in `retraining_manager.py`.
- [ ] Expand training data in `ml_data_preparer.py` (e.g., add more features like Bollinger Bands, ATR).
- [ ] Implement parameter adaptation (leverage, trade_percentage, margin_multiplier) in `start_trading_all.py`.
- [ ] Add genetic algorithm optimization in `strategy_optimizer.py`.

### Milestone 3: Market X-Ray System
- [ ] Add Bollinger Bands and ATR in `signal_generator_indicators.py`.
- [ ] Implement correlation analysis in `market_analyzer.py`.
- [ ] Add news analysis in `news_analyzer.py`.

### Milestone 4: Scalability for 1000+ Users
- [ ] Test system with 1000+ users.
- [ ] Optimize Redis (increase `maxmemory`, add clustering).
- [ ] Add rate limiting in `exchange_pool.py`.

### Milestone 5: Additional Features
- [ ] Add Telegram notifications in `notification_manager.py`.
- [ ] Implement unit tests for critical components.

## Next Steps (Immediate)
1. **Fix `collect_training_data`**:
   - Investigate why `fetch_my_trades` returns an empty list for `user1` and `user2`.
   - If no trades are available, consider using historical trades for a specific symbol (e.g., `BTCUSDT`) as a fallback.
2. **Fix Symbol Filtering**:
   - Add more debug logging in `filter_symbols` to identify the exact cause of the failure on `TGTUSDT`.
   - Check `backtest_results.json` for potential data corruption or missing entries.
3. **Start Trading**:
   - Ensure trading starts for `user1` with filtered symbols.
