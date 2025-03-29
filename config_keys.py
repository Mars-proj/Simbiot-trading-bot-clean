# API keys for users and exchanges
# Keys are indexed by a unique user ID (UUID)
API_KEYS = {
    "8d99788d-f58f-4fb8-9e4d-c05f177f5405": {
        'mexc': {
            'api_key': 'mx0vgl3dueS536E23l',
            'api_secret': 'a08af67cb36b45b7a301adcd6faac3f6',
            'enableRateLimit': True,
        },
    },
    # Новые пользователи могут быть добавлены сюда в формате:
    # "user_id": {
    #     'exchange_name': {
    #         'api_key': 'your_api_key',
    #         'api_secret': 'your_api_secret',
    #         'enableRateLimit': True,
    #     },
    # },
}

# Preferred exchanges for each user
# Indexed by user ID (UUID)
PREFERRED_EXCHANGES = {user_id: 'mexc' for user_id in API_KEYS.keys()}

# Validate API keys
def validate_api_keys(logger_main):
    """Validates API keys to ensure they are properly configured"""
    for user, exchanges in API_KEYS.items():
        for exchange, creds in exchanges.items():
            if not creds.get('api_key') or not creds.get('api_secret'):
                logger_main.error(f"Invalid API key configuration for user {user} on exchange {exchange}")
                raise ValueError(f"Invalid API key configuration for user {user} on exchange {exchange}")

# List of supported exchanges
SUPPORTED_EXCHANGES = ['mexc', 'binance', 'bybit', 'kucoin', 'okx']

__all__ = ['API_KEYS', 'PREFERRED_EXCHANGES', 'validate_api_keys', 'SUPPORTED_EXCHANGES']
