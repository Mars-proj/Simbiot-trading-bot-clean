from prometheus_client import Counter, Gauge, start_http_server

trades_total = Counter('trades_total', 'Total number of trades executed', ['user'])
balance_gauge = Gauge('user_balance_usdt', 'Current USDT balance', ['user'])

def start_monitoring(port=8000):
    """
    Start Prometheus monitoring server.

    Args:
        port (int): Port to run the server on (default: 8000).
    """
    start_http_server(port)

def record_trade(user):
    """
    Record a trade in Prometheus metrics.

    Args:
        user: User identifier.
    """
    trades_total.labels(user=user).inc()

def update_balance(user, balance):
    """
    Update user balance in Prometheus metrics.

    Args:
        user: User identifier.
        balance: Current balance in USDT.
    """
    balance_gauge.labels(user=user).set(balance)
