import aiosmtplib
from email.mime.text import MIMEText
from telegram_notifier import TelegramNotifier

class NotificationManager:
    """
    Manage notifications via email and Telegram.
    """

    def __init__(self, smtp_server="smtp.gmail.com", smtp_port=587, sender_email="your_email@gmail.com", password="your_password", telegram_bot_token=None, telegram_chat_id=None):
        """
        Initialize the notification manager.

        Args:
            smtp_server (str): SMTP server (default: "smtp.gmail.com").
            smtp_port (int): SMTP port (default: 587).
            sender_email (str): Sender email address.
            password (str): Sender email password.
            telegram_bot_token (str): Telegram bot token (optional).
            telegram_chat_id (str): Telegram chat ID (optional).
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.password = password
        self.telegram = TelegramNotifier(telegram_bot_token, telegram_chat_id) if telegram_bot_token and telegram_chat_id else None

    async def send_email(self, recipient, subject, body):
        """
        Send an email notification.

        Args:
            recipient (str): Recipient email.
            subject (str): Email subject.
            body (str): Email body.
        """
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = recipient

        server = aiosmtplib.SMTP(hostname=self.smtp_server, port=self.smtp_port)
        await server.connect()
        await server.starttls()
        await server.login(self.sender_email, self.password)
        await server.send_message(msg)
        await server.quit()

    async def send_telegram(self, message):
        """
        Send a Telegram notification.

        Args:
            message (str): Message to send.
        """
        if self.telegram:
            await self.telegram.send_message(message)

    async def notify(self, recipient, subject, body):
        """
        Send a notification via email and Telegram.

        Args:
            recipient (str): Recipient email.
            subject (str): Notification subject.
            body (str): Notification body.
        """
        await self.send_email(recipient, subject, body)
        if self.telegram:
            await self.send_telegram(f"{subject}\n{body}")
