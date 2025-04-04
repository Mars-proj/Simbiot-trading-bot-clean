# Graphical Map of Trading Bot System

This graphical map represents the structure and interactions of the Trading Bot system modules. It can be visualized using Mermaid (e.g., in GitHub or a compatible Markdown viewer).

```mermaid
graph TD
    A[main.py] -->|Runs| B[process_users]
    B -->|Fetches Symbols| C[test_symbols.py]
    C -->|Saves| D[selected_pairs.json]
    B -->|Runs Backtests| E[run_backtests]
    E -->|Saves| F[backtest_results.json]
    B -->|Processes Users| G[run_trading_for_user]
    G -->|Filters Symbols| H[filter_symbols]
    H -->|Uses| F
    G -->|Starts Trading| I[start_trading_all.py]
    G -->|Cleans Up| J[trade_pool_manager.py]
    G -->|Monitors Positions| K[position_monitor.py]
    G -->|Retrains Model| L[retraining_manager.py]
    L -->|Loads Data| M[data_loader]
    M -->|Fetches Historical Data| N[historical_data_fetcher.py]
    M -->|Collects Trade Data| O[data_collector.py]
    M -->|Prepares ML Data| P[ml_data_preparer.py]
    P -->|Extracts Features| Q[features.py]
    P -->|Normalizes Features| R[ml_data_preparer_utils.py]
    L -->|Trains Model| S[ml_model_trainer.py]
    S -->|Saves| T[models/trading_model.pth]
    G -->|Uses| U[exchange_pool.py]
    U -->|Manages| V[Exchange Instances]
