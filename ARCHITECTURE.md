# Simbiot Trading Bot Architecture

Below is the updated architecture diagram of the Simbiot Trading Bot, showing the interaction between components.

```mermaid
graph TD
    A[Core.py] -->|Schedules Tasks| B[Celery App]
    B -->|Processes Users| C[Redis Queue]
    C -->|Distributes Tasks| D[Celery Workers]
    D -->|Fetches Market Data| E[Exchange Pool]
    E -->|Interacts with| F[MEXC API]
    D -->|Analyzes Market| G[Market State Analyzer]
    D -->|Filters Symbols| H[Symbol Filter]
    D -->|Generates Signals| I[Strategy Manager]
    I -->|Executes Trades| J[Start Trading All]
    J -->|Sends Orders| F
    A -->|Logs Metrics| K[Redis Storage]
    K -->|Stores User Data| L[User Manager]
    J -->|Logs Signals| M[Trading Log]
