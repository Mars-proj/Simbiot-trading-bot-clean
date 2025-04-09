import aiohttp

class TelegramNotifier:
    """
    Send notifications via Telegram.
    """

    def __init__(self, bot_token, chat_id):
        """
        Initialize the Telegram notifier.

        Args:
            bot_token (str): Telegram bot token.
            chat_id (str): Telegram chat ID.
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    async def send_message(self, message):
        """
        Send a message via Telegram.

        Args:
            message (str): Message to send.

        Returns:
            dict: Response from Telegram API.
        """
        async with aiohttp.ClientSession() as session:
            payload = {"chat_id": self.chat_id, "text": message}
            async with session.post(self.url, json=payload) as response:
                return await response.json()
