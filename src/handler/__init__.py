import logging
from sqlmodel.ext.asyncio.session import AsyncSession

import httpx

from models import WhatsAppWebhookPayload
from .base_handler import BaseHandler

logger = logging.getLogger(__name__)

SLACK_WEBHOOK_URL = "https://hooks.slack.com/triggers/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"


class MessageHandler(BaseHandler):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def __call__(self, payload: WhatsAppWebhookPayload):
        """Process incoming WhatsApp message: log to console, store in database, and send to Slack"""
        # Store the message in the database
        message = await self.store_message(payload)

        if message and message.text:
            # Log the message content to console
            logger.info(f"Received WhatsApp message: {message.text}")
            logger.info(f"From: {message.sender_jid}, Chat: {message.chat_jid}")

            if message.media_url:
                logger.info(f"Media URL: {message.media_url}")

            # Send message to Slack only if it's from a group
            if message.group_jid:
                try:
                    async with httpx.AsyncClient() as client:
                        slack_payload = {
                            "sender": f'{message.sender_jid} - {payload.pushname}',
                            "content": message.text
                        }
                        response = await client.post(
                            SLACK_WEBHOOK_URL,
                            json=slack_payload,
                            headers={"Content-Type": "application/json"}
                        )
                        response.raise_for_status()
                        logger.info("Successfully sent group message to Slack")
                except Exception as e:
                    logger.error(f"Failed to send message to Slack: {e}")
            else:
                logger.info("Skipping Slack notification for direct message")
        else:
            logger.info(f"Received WhatsApp message without text content: {payload.model_dump_json()}")
