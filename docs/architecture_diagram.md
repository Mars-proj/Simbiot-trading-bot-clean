# Architecture Diagram

Below is the architecture diagram of the Simbiot Trading Bot system, illustrating the main components and their interactions.

```mermaid
graph TD
    A[Core.py] -->|Manages cycles| B[UserManager.py]
    A -->|Processes users| C[ExchangePool.py]
    A -->|Analyzes market| D[MarketStateAnalyzer.py]
    A -->|Executes trades| E[StartTradingAll.py]
    D -->|Returns market type| A
    E -->|Fetches data| F[HistoricalDataFetcher.py]
    E -->|Selects strategy| G[StrategyManager.py]
    G -->|Uses indicators| H[Indicators/*]
    G -->|Optimizes strategies| I[Learning/StrategyOptimizer.py]
    I -->|Backtests| J[Learning/Backtester.py]
    I -->|Evaluates trades| K[Learning/TradeEvaluator.py]
    E -->|Stores trade success| L[Redis]
    C -->|Interacts with| M[MEXC API]
