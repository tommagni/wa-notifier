import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from api.deps import get_handler
from handler import MessageHandler
from models.webhook import WhatsAppWebhookPayload

logger = logging.getLogger(__name__)

# Create router for webhook endpoints
router = APIRouter(tags=["webhook"])


@router.post("/webhook")
async def webhook(
    payload: WhatsAppWebhookPayload,
    handler: Annotated[MessageHandler, Depends(get_handler)],
) -> str:
    """
    WhatsApp webhook endpoint for receiving incoming messages.
    Returns:
        Simple "ok" response to acknowledge receipt
    """
    # Only process messages that have a sender (from_ field) and actual content
    if payload.from_:
        if should_process_message(payload):
            await handler(payload)
        else:
            logger.info(
                f"Skipping message from {payload.from_} "
                f"at {payload.timestamp} because it doesn't have text content or has less than 2 words"
            )

    return "ok"


def should_process_message(payload: WhatsAppWebhookPayload) -> bool:
    """
    Check if the webhook payload contains text content.
    Only processes pure text messages with more than 2 words, filters out media, reactions, and other message types.
    """
    # Only process text messages - no media, no reactions, no special content types
    if not payload.message or not payload.message.text:
        return False

    # Only process messages with more than 2 words
    word_count = len(payload.message.text.strip().split())
    return word_count > 2
