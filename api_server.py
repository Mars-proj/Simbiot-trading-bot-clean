from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from logging_setup import logger_main
import os
import time

app = FastAPI()

# API key authentication
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Configurable API keys and rate limits
API_KEYS = os.getenv("API_KEYS", "test_key").split(",")
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", 100))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", 60))  # in seconds

# Rate limiting storage (in-memory for simplicity)
request_counts = {}

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verifies the API key and enforces rate limiting."""
    if api_key not in API_KEYS:
        logger_main.error(f"Invalid API key: {api_key}")
        raise HTTPException(status_code=403, detail="Invalid API key")

    # Rate limiting
    current_time = int(time.time())
    if api_key not in request_counts:
        request_counts[api_key] = []
    
    # Remove requests outside the time window
    request_counts[api_key] = [t for t in request_counts[api_key] if current_time - t < RATE_LIMIT_WINDOW]
    
    # Check rate limit
    if len(request_counts[api_key]) >= RATE_LIMIT_REQUESTS:
        logger_main.warning(f"Rate limit exceeded for API key {api_key}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Add current request timestamp
    request_counts[api_key].append(current_time)
    return api_key

@app.get("/health")
async def health_check(api_key: str = Security(verify_api_key)):
    """Health check endpoint."""
    logger_main.info("Health check requested")
    return {"status": "healthy"}

__all__ = ['app']
