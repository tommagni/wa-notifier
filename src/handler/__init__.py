import logging
from sqlmodel.ext.asyncio.session import AsyncSession

from models import WhatsAppWebhookPayload
from .base_handler import BaseHandler

logger = logging.getLogger(__name__)


class MessageHandler(BaseHandler):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def __call__(self, payload: WhatsAppWebhookPayload):
        """Process incoming WhatsApp message: log to console and store in database"""
        # Store the message in the database
        message = await self.store_message(payload)

        if message and message.text:
            # Log the message content to console
            logger.info(f"Received WhatsApp message: {message.text}")
            logger.info(f"From: {message.sender_jid}, Chat: {message.chat_jid}")

            if message.media_url:
                logger.info(f"Media URL: {message.media_url}")
        else:
            logger.info(f"Received WhatsApp message without text content: {payload.model_dump_json()}")
