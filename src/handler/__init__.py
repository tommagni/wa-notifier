import logging
from sqlmodel.ext.asyncio.session import AsyncSession

import httpx

from models import WhatsAppWebhookPayload
from config import Settings
from whatsapp.jid import parse_jid
from .base_handler import BaseHandler
from .relevance_checker import should_notify

logger = logging.getLogger(__name__)


class MessageHandler(BaseHandler):
    def __init__(self, session: AsyncSession, settings: Settings):
        super().__init__(session)
        self.settings = settings

    def _extract_group_jid(self, payload: WhatsAppWebhookPayload) -> str | None:
        """Extract group JID from payload if it's a group message."""
        if not payload.from_:
            return None

        # Parse sender and chat JIDs from the 'from_' field
        if " in " in payload.from_:
            sender_jid, chat_jid = payload.from_.split(" in ")
        else:
            chat_jid = payload.from_

        # Parse the chat JID to check if it's a group
        jid = parse_jid(chat_jid)
        if jid.is_group():
            return str(jid.to_non_ad())
        return None

    async def __call__(self, payload: WhatsAppWebhookPayload):
        """Process incoming WhatsApp message: log to console, store in database, and send to Slack"""
        # Log the entire incoming payload for debugging
        logger.info(f"Incoming WhatsApp payload: {payload.model_dump_json()}")

        # Check if we should limit to a specific group before storing
        if self.settings.limit_to_group_id:
            group_jid = self._extract_group_jid(payload)
            if group_jid and group_jid != self.settings.limit_to_group_id:
                logger.info(f"Ignoring message from group {group_jid} - limited to group {self.settings.limit_to_group_id}")
                return

        # Store the message in the database
        message = await self.store_message(payload, payload=payload)

        # Load group relationship if it's a group message
        if message and message.group_jid:
            await self.session.refresh(message, ["group"])

        if message and message.text:
            # Log the message content to console
            logger.info("Received WhatsApp message: %s", message.text)
            logger.info("From: %s, Chat: %s", message.sender_jid, message.chat_jid)

            if message.media_url:
                logger.info("Media URL: %s", message.media_url)

            # Send message to Slack only if it's from a group and should be notified about
            if message.group_jid:
                # Check if this message should trigger a notification using LangChain
                should_send_notification, reasoning, total_tokens, input_tokens, output_tokens = await should_notify(message.text)
                logger.info("Should send notification: %s (reasoning: %s, total: %s, input: %s, output: %s)",
                           should_send_notification, reasoning, total_tokens, input_tokens, output_tokens)

                # Update the message with relevance flag, reasoning, and token counts
                message.is_relevant = should_send_notification
                message.reasoning = reasoning
                message.relevancy_total_token_count = total_tokens
                message.relevancy_input_tokens = input_tokens
                message.relevancy_output_tokens = output_tokens
                self.session.add(message)
                await self.session.commit()

                if should_send_notification:
                    try:
                        async with httpx.AsyncClient() as client:
                            group_name = message.group.group_name if message.group and message.group.group_name else "Unknown Group"
                            slack_payload = {
                                "sender": f'{message.sender_jid} - {payload.pushname} ({group_name})',
                                "content": message.text
                            }
                            response = await client.post(
                                self.settings.slack_webhook_url,
                                json=slack_payload,
                                headers={"Content-Type": "application/json"}
                            )
                            response.raise_for_status()
                            logger.info("Successfully sent group message to Slack")
                    except Exception:
                        logger.exception("Failed to send message to Slack")
                else:
                    logger.info("Skipping Slack notification - message doesn't match recruitment criteria")
            else:
                logger.info("Skipping Slack notification for direct message")
        else:
            logger.info("Received WhatsApp message without text content: %s",
                       payload.model_dump_json())
