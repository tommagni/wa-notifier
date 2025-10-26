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
        if _has_content(payload):
            await handler(payload)
        else:
            logger.debug(
                f"Skipping non-text message from {payload.from_} "
                f"at {payload.timestamp}"
            )

    return "ok"


def _has_content(payload: WhatsAppWebhookPayload) -> bool:
    """
    Check if the webhook payload contains text content.
    Only processes pure text messages, filters out media, reactions, and other message types.
    """
    # Only process text messages - no media, no reactions, no special content types
    return bool(payload.message and payload.message.text)
