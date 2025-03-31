from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from logging_setup import logger_main
import uvicorn
import time
from collections import defaultdict

app = FastAPI()

class APIServer:
    """Manages the API server with authentication and rate limiting."""
    def __init__(self, valid_api_keys=None, rate_limit=100, rate_limit_window=60):
        self.valid_api_keys = valid_api_keys if valid_api_keys is not None else ["simbiot-api-key-123"]
        self.rate_limit = rate_limit  # Maximum requests per window
        self.rate_limit_window = rate_limit_window  # Window in seconds
        self.request_counts = defaultdict(list)  # {api_key: [(timestamp, count)]}
        logger_main.info(f"Initialized API server with rate limit {self.rate_limit} requests per {self.rate_limit_window} seconds")

    def check_rate_limit(self, api_key):
        """Checks if the API key has exceeded the rate limit."""
        current_time = time.time()
        # Remove requests older than the rate limit window
        self.request_counts[api_key] = [t for t in self.request_counts[api_key] if current_time - t < self.rate_limit_window]
        # Count requests in the current window
        request_count = len(self.request_counts[api_key])
        if request_count >= self.rate_limit:
            logger_main.error(f"Rate limit exceeded for API key: {api_key}")
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        # Add the current request timestamp
        self.request_counts[api_key].append(current_time)

api_server = APIServer()

# API key authentication
api_key_header = APIKeyHeader(name="X-API-Key")

@app.get("/status")
async def get_status(api_key: str = Security(api_key_header)):
    """Returns the status of the trading bot."""
    try:
        # Validate API key
        if api_key not in api_server.valid_api_keys:
            logger_main.error(f"Invalid API key: {api_key}")
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Check rate limit
        api_server.check_rate_limit(api_key)

        logger_main.info(f"Status request received for API key: {api_key}")
        return {"status": "running"}
    except Exception as e:
        logger_main.error(f"Error in status endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
