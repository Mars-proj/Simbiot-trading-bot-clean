from logging_setup import logger_main
from utils import log_exception
from json_handler import dumps, loads
from redis_initializer import redis_client

async def update_available_tokens(user_id, tokens, ttl_seconds, available_tokens_key_prefix):
    if redis_client is None:
        logger_main.error("redis_client is not initialized")
        raise ValueError("redis_client is not initialized")
    logger_main.info(f"Updating available tokens for user {user_id}")
    try:
        key = f"{available_tokens_key_prefix}{user_id}"
        token_dict = {token: 1 for token in tokens}
        await redis_client.setex(key, ttl_seconds, dumps(token_dict))
    except Exception as e:
        logger_main.error(f"Error updating available tokens for user {user_id}: {str(e)}")
        log_exception(f"Error updating available tokens: {str(e)}", e)

async def get_available_tokens(user_id, available_tokens_key_prefix):
    if redis_client is None:
        logger_main.error("redis_client is not initialized")
        raise ValueError("redis_client is not initialized")
    logger_main.info(f"Fetching available tokens for user {user_id}")
    try:
        key = f"{available_tokens_key_prefix}{user_id}"
        token_data = await redis_client.get(key)
        if token_data:
            token_dict = loads(token_data)
            return {token: amount for token, amount in token_dict.items() if amount > 0}
        return {'USDT': 1}
    except Exception as e:
        logger_main.error(f"Error fetching available tokens for user {user_id}: {str(e)}")
        log_exception(f"Error fetching available tokens: {str(e)}", e)
        return {'USDT': 1}

__all__ = ['update_available_tokens', 'get_available_tokens']
