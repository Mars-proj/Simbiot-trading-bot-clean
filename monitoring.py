from prometheus_client import Counter, Histogram, start_http_server
import logging

logger = logging.getLogger(__name__)

# Define Prometheus metrics
trade_requests = Counter('trade_requests_total', 'Total number of trade requests')
trade_latency = Histogram('trade_latency_seconds', 'Trade request latency in seconds')

# Start Prometheus HTTP server
start_http_server(8000)
logger.info("Prometheus metrics server started on port 8000")

def monitor_trade_request():
    """
    Monitor a trade request by incrementing the counter and observing latency.
    """
    trade_requests.inc()
    with trade_latency.time():
        logger.info("Monitoring trade request")
