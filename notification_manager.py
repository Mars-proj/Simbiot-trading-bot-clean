import aiosmtplib
from email.mime.text import MIMEText
import logging

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self, smtp_host="smtp.protonmail.com", smtp_port=587, smtp_user=None, smtp_password=None):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        
        # Проверка обязательных параметров
        if not self.smtp_user or not self.smtp_password:
            raise ValueError("smtp_user and smtp_password must be provided")

    async def send_email(self, to_email, subject, body):
        """
        Send a message to the specified email address.

        Args:
            to_email: Recipient email address.
            subject: Email subject.
            body: Email body.
        """
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = self.smtp_user
        msg['To'] = to_email

        try:
            smtp = aiosmtplib.SMTP(hostname=self.smtp_host, port=self.smtp_port, use_tls=True)
            await smtp.connect()
            await smtp.login(self.smtp_user, self.smtp_password)
            await smtp.send_message(msg)
            await smtp.quit()
            logger.info(f"Email sent to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            raise
