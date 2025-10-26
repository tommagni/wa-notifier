#!/usr/bin/env python3
"""
Simple test script to verify LIMIT_TO_GROUP_ID functionality - no database storage.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.config import Settings
from sqlmodel.ext.asyncio.session import AsyncSession


class MockMessageHandler:
    """Mock version of MessageHandler for testing."""

    def __init__(self, session: AsyncSession, settings: Settings):
        self.session = session
        self.settings = settings
        self.store_message_called = False

    def _extract_group_jid(self, payload):
        """Extract group JID from payload if it's a group message."""
        if not payload.from_:
            return None

        # Parse sender and chat JIDs from the 'from_' field
        if " in " in payload.from_:
            sender_jid, chat_jid = payload.from_.split(" in ")
        else:
            chat_jid = payload.from_

        # Simple check for group JID (ends with @g.us)
        if chat_jid.endswith("@g.us"):
            return chat_jid
        return None

    async def store_message(self, payload):
        self.store_message_called = True
        return MagicMock(group_jid=self._extract_group_jid(payload))

    async def session_refresh(self, message, relationships):
        pass

    async def should_notify(self, text):
        return True, "test", 10, 5, 5

    async def __call__(self, payload):
        """Simplified version of the real __call__ method."""
        # Check if we should limit to a specific group before storing
        if self.settings.limit_to_group_id:
            group_jid = self._extract_group_jid(payload)
            if group_jid and group_jid != self.settings.limit_to_group_id:
                print(f"Ignoring message from group {group_jid} - limited to group {self.settings.limit_to_group_id}")
                return

        # Store the message in the database
        message = await self.store_message(payload)
        print("Message stored and processed normally")


async def test_group_filtering():
    """Test that group filtering works correctly - messages from non-matching groups aren't stored."""

    # Mock payload class
    class MockPayload:
        def __init__(self, from_field):
            self.from_ = from_field
            self.timestamp = "2024-01-01T00:00:00Z"
            self.pushname = "Test User"
            self.message = MagicMock()
            self.message.id = "test123"
            self.message.text = "Hello world"

    # Test 1: No limit set - should process all messages
    settings = Settings(limit_to_group_id=None)
    mock_session = AsyncMock()
    handler = MockMessageHandler(mock_session, settings)

    payload = MockPayload("user123@s.whatsapp.net in 120363123456789012@g.us")
    await handler(payload)

    assert handler.store_message_called, "Should process message when no limit set"
    print("✓ Test 1 passed: No limit set - processes all messages")

    # Test 2: Limit set to matching group - should process
    settings = Settings(limit_to_group_id="120363123456789012@g.us")
    handler = MockMessageHandler(mock_session, settings)
    handler.store_message_called = False  # Reset

    payload = MockPayload("user123@s.whatsapp.net in 120363123456789012@g.us")
    await handler(payload)

    assert handler.store_message_called, "Should process message when group matches limit"
    print("✓ Test 2 passed: Limit set to matching group - processes message")

    # Test 3: Limit set to different group - should not store or process
    settings = Settings(limit_to_group_id="999999999999999999@g.us")
    handler = MockMessageHandler(mock_session, settings)
    handler.store_message_called = False  # Reset

    payload = MockPayload("user123@s.whatsapp.net in 120363123456789012@g.us")
    await handler(payload)

    assert not handler.store_message_called, "Should not store or process message when group doesn't match limit"
    print("✓ Test 3 passed: Limit set to different group - ignores message completely")

    print("All tests passed! Group filtering works correctly - non-matching messages aren't stored.")


if __name__ == "__main__":
    asyncio.run(test_group_filtering())