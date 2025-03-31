import smtplib
from email.mime.text import MIMEText
from logging_setup import logger_main
import os

class NotificationManager:
    def __init__(self):
        self.settings = {
            "email": {
                "enabled": os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "false").lower() == "true",
                "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
                "smtp_port": int(os.getenv("SMTP_PORT", 587)),
                "sender_email": os.getenv("SENDER_EMAIL", ""),
                "sender_password": os.getenv("SENDER_PASSWORD", ""),
                "receiver_email": os.getenv("RECEIVER_EMAIL", ""),
            }
        }

    async def send_email(self, subject, message):
        """Sends an email notification."""
        try:
            if not self.settings["email"]["enabled"]:
                logger_main.warning("Email notifications are disabled")
                return False

            # Validate email settings
            if not all([
                self.settings["email"]["sender_email"],
                self.settings["email"]["sender_password"],
                self.settings["email"]["receiver_email"]
            ]):
                logger_main.error("Email notification settings are incomplete")
                return False

            # Create email message
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = self.settings["email"]["sender_email"]
            msg['To'] = self.settings["email"]["receiver_email"]

            # Send email
            with smtplib.SMTP(self.settings["email"]["smtp_server"], self.settings["email"]["smtp_port"]) as server:
                server.starttls()
                server.login(self.settings["email"]["sender_email"], self.settings["email"]["sender_password"])
                server.send_message(msg)

            logger_main.info(f"Email notification sent: Subject='{subject}'")
            return True
        except Exception as e:
            logger_main.error(f"Error sending email notification: {e}")
            return False

    async def notify(self, subject, message):
        """Sends a notification using available methods."""
        try:
            # Currently only email is supported
            if self.settings["email"]["enabled"]:
                return await self.send_email(subject, message)
            else:
                logger_main.warning("No notification methods are enabled")
                return False
        except Exception as e:
            logger_main.error(f"Error sending notification: {e}")
            return False

__all__ = ['NotificationManager']
