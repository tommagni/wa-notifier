import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from api.deps import get_handler, get_db_async_session
from handler import MessageHandler
from models import Message
from models.webhook import WhatsAppWebhookPayload

logger = logging.getLogger(__name__)

# Create router for webhook endpoints
router = APIRouter(tags=["webhook"])


@router.post("/webhook")
async def webhook(
    payload: WhatsAppWebhookPayload,
    handler: Annotated[MessageHandler, Depends(get_handler)],
    session: Annotated[AsyncSession, Depends(get_db_async_session)],
) -> str:
    """
    WhatsApp webhook endpoint for receiving incoming messages.
    Returns:
        Simple "ok" response to acknowledge receipt
    """
    # Only process messages that have a sender (from_ field) and actual content
    if payload.from_:
        if not await should_process_message(payload, session):
            return "ok"

        await handler(payload)

    return "ok"


async def should_process_message(payload: WhatsAppWebhookPayload, session: AsyncSession) -> bool:
    """
    Check if the webhook payload should be processed.
    Filters out:
    - Messages older than 4 days
    - Media, reactions, and other non-text message types
    - Messages with less than 3 words
    - Duplicate messages (already in database)
    """
    # Skip messages older than 4 days
    if payload.timestamp < datetime.now(timezone.utc) - timedelta(days=4):
        logger.info("Skipping message from %s at %s - older than 4 days", payload.from_, payload.timestamp)
        return False

    # Only process text messages - no media, no reactions, no special content types
    if not payload.message or not payload.message.text:
        logger.info("Skipping message from %s - no text content", payload.from_)
        return False

    # Only process messages with more than 2 words
    word_count = len(payload.message.text.strip().split())
    if word_count <= 2:
        logger.info("Skipping message from %s - only %s words", payload.from_, word_count)
        return False

    # Skip duplicate messages (already in database)
    message_id = payload.message.id
    existing_message = await session.get(Message, message_id)
    if existing_message:
        logger.info("Skipping message %s - already exists in database", message_id)
        return False

    return True
