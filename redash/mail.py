"""
Custom Flask-Mail backends for sending emails via different providers.
"""

import logging
from email import message_from_string

import boto3
from flask_mail import BaseMailClass

logger = logging.getLogger(__name__)


class SESMailBackend(BaseMailClass):
    """Flask-Mail backend using AWS SES via boto3 with instance profile."""

    def __init__(self, app=None):
        super().__init__(app)
        self.ses_client = None

    def init_app(self, app, **kwargs):
        super().init_app(app, **kwargs)
        try:
            self.ses_client = boto3.client("ses")
            logger.info("SES mail backend initialized")
        except Exception as e:
            logger.error(f"Failed to initialize SES client: {e}")
            raise

    def send(self, message, **kwargs):
        """Send email via AWS SES."""
        if not self.ses_client:
            try:
                self.ses_client = boto3.client("ses")
            except Exception as e:
                logger.error(f"Failed to create SES client: {e}")
                raise

        try:
            msg = message_from_string(message.as_string())

            # Extract recipients
            recipients = set()
            if message.recipients:
                recipients.update(message.recipients)
            if message.cc:
                recipients.update(message.cc)
            if message.bcc:
                recipients.update(message.bcc)

            if not recipients:
                logger.warning("No recipients specified for email")
                return False

            # Get sender
            sender = message.sender or self.app.config.get("MAIL_DEFAULT_SENDER")
            if not sender:
                logger.error("No sender specified for email")
                return False

            # Send via SES
            self.ses_client.send_raw_email(
                Source=sender,
                Destinations=list(recipients),
                RawMessage={"Data": message.as_string()},
            )

            logger.info(f"Email sent via SES to {recipients}")
            return True

        except Exception as e:
            logger.exception(f"Failed to send email via SES: {e}")
            raise
