import logging
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from api.webhook import webhook, should_process_message
from config import Settings
from handler import MessageHandler
from models import Message
from models.webhook import WhatsAppWebhookPayload
from models.webhook import Message as PayloadMessage
from test_utils.mock_session import AsyncSessionMock


logger = logging.getLogger(__name__)


@pytest.fixture
def mock_settings():
    """Create mock settings for testing"""
    settings = MagicMock(spec=Settings)
    settings.limit_to_group_id = None
    settings.slack_webhook_url = "https://hooks.slack.com/test"
    return settings


@pytest.fixture
def sample_payload():
    """Create a sample WhatsApp webhook payload"""
    return WhatsAppWebhookPayload(
        from_="972546150790:16@s.whatsapp.net in 120363365283777509@g.us",
        timestamp=datetime.now(timezone.utc),
        pushname="Test User",
        message=PayloadMessage(
            id="TEST_MESSAGE_ID_123",
            text="Looking for a Python developer for our startup",
        ),
    )


@pytest.mark.asyncio
async def test_should_process_message_rejects_duplicate(sample_payload):
    """Test that should_process_message returns False when message exists"""
    mock_session = AsyncSessionMock()

    # Create an existing message
    existing_message = Message(
        message_id="TEST_MESSAGE_ID_123",
        text="Looking for a Python developer for our startup",
        chat_jid="120363365283777509@g.us",
        sender_jid="972546150790:16@s.whatsapp.net",
        timestamp=datetime.now(timezone.utc),
        group_jid="120363365283777509@g.us",
    )

    # Mock session.get to return the existing message
    mock_session.get = AsyncMock(return_value=existing_message)

    # Check if should process
    should_process = await should_process_message(sample_payload, mock_session)

    assert should_process is False
    mock_session.get.assert_called_once_with(Message, "TEST_MESSAGE_ID_123")


@pytest.mark.asyncio
async def test_should_process_message_accepts_new_message(sample_payload):
    """Test that should_process_message returns True when message doesn't exist"""
    mock_session = AsyncSessionMock()

    # Mock session.get to return None (message doesn't exist)
    mock_session.get = AsyncMock(return_value=None)

    # Check if should process
    should_process = await should_process_message(sample_payload, mock_session)

    assert should_process is True
    mock_session.get.assert_called_once_with(Message, "TEST_MESSAGE_ID_123")


@pytest.mark.asyncio
async def test_should_process_message_rejects_short_messages():
    """Test that should_process_message returns False for messages with <= 2 words"""
    mock_session = AsyncSessionMock()

    payload = WhatsAppWebhookPayload(
        from_="972546150790:16@s.whatsapp.net in 120363365283777509@g.us",
        timestamp=datetime.now(timezone.utc),
        pushname="Test User",
        message=PayloadMessage(
            id="TEST_MESSAGE_ID_123",
            text="Short msg",  # Only 2 words
        ),
    )

    # Check if should process
    should_process = await should_process_message(payload, mock_session)

    assert should_process is False
    # session.get should not be called if message is too short
    mock_session.get.assert_not_called()


@pytest.mark.asyncio
async def test_webhook_skips_duplicate_message(sample_payload, mock_settings):
    """Test that webhook endpoint skips processing duplicate messages"""
    mock_session = AsyncSessionMock()

    # Create an existing message
    existing_message = Message(
        message_id="TEST_MESSAGE_ID_123",
        text="Looking for a Python developer for our startup",
        chat_jid="120363365283777509@g.us",
        sender_jid="972546150790:16@s.whatsapp.net",
        timestamp=datetime.now(timezone.utc),
        group_jid="120363365283777509@g.us",
    )

    # Mock session.get to return the existing message (duplicate)
    mock_session.get = AsyncMock(return_value=existing_message)

    # Create a mock handler (without spec to avoid initialization issues)
    mock_handler = AsyncMock()

    # Call webhook
    response = await webhook(sample_payload, mock_handler, mock_session)

    # Verify handler was NOT called (message is duplicate)
    mock_handler.assert_not_called()

    # Verify response is "ok"
    assert response == "ok"


@pytest.mark.asyncio
async def test_webhook_processes_new_message(sample_payload, mock_settings):
    """Test that webhook endpoint processes new (non-duplicate) messages"""
    mock_session = AsyncSessionMock()

    # Mock session.get to return None (message doesn't exist)
    mock_session.get = AsyncMock(return_value=None)

    # Create a mock handler (without spec to avoid initialization issues)
    mock_handler = AsyncMock()

    # Call webhook
    response = await webhook(sample_payload, mock_handler, mock_session)

    # Verify handler WAS called (message is new)
    mock_handler.assert_called_once_with(sample_payload)

    # Verify response is "ok"
    assert response == "ok"

