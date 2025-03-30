from fastapi import FastAPI, HTTPException, Header
from logging_setup import logger_main
from typing import Dict
import time

app = FastAPI()

# In-memory storage for API keys and rate limiting
API_KEYS: Dict[str, str] = {
    "test_key": "user1"
}
RATE_LIMITS: Dict[str, list] = {}  # {api_key: [timestamps]}
RATE_LIMIT_WINDOW = 60  # 60 seconds
RATE_LIMIT_MAX_REQUESTS = 100  # Max 100 requests per minute

def validate_api_key(api_key: str = Header(...)):
    """Validates the API key provided in the request header."""
    if api_key not in API_KEYS:
        logger_main.error(f"Invalid API key: {api_key}")
        raise HTTPException(status_code=401, detail="Invalid API key")
    return API_KEYS[api_key]

def rate_limit(api_key: str):
    """Enforces rate limiting for the API key."""
    current_time = time.time()
    if api_key not in RATE_LIMITS:
        RATE_LIMITS[api_key] = []

    # Remove timestamps older than the window
    RATE_LIMITS[api_key] = [ts for ts in RATE_LIMITS[api_key] if current_time - ts < RATE_LIMIT_WINDOW]

    # Check rate limit
    if len(RATE_LIMITS[api_key]) >= RATE_LIMIT_MAX_REQUESTS:
        logger_main.warning(f"Rate limit exceeded for API key {api_key}: {len(RATE_LIMITS[api_key])} requests")
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Add current timestamp
    RATE_LIMITS[api_key].append(current_time)

@app.get("/status")
async def get_status(user_id: str = Header(...)):
    """Returns the status for the user."""
    user = validate_api_key(user_id)
    rate_limit(user_id)
    logger_main.info(f"Fetched status for user {user}")
    return {"status": "active", "user_id": user}

__all__ = ['app']
