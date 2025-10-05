import logging

from sqlmodel.ext.asyncio.session import AsyncSession

from models import (
    WhatsAppWebhookPayload,
    BaseGroup,
    BaseSender,
    Message,
    Sender,
    Group,
    BaseMessage,
    upsert,
)

logger = logging.getLogger(__name__)


class BaseHandler:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def store_message(
        self,
        message: Message | BaseMessage | WhatsAppWebhookPayload,
        sender_pushname: str | None = None,
    ) -> Message | None:
        """
        Store a message in the database
        :param message:  Message to store - can be a Message, BaseMessage or WhatsAppWebhookPayload
        :param sender_pushname:  Pushname of the sender [Optional]
        :return: The stored message
        """
        if isinstance(message, WhatsAppWebhookPayload):
            sender_pushname = message.pushname
            message = Message.from_webhook(message)
        if isinstance(message, BaseMessage):
            message = Message(**message.model_dump())

        # Store all messages, even those without text (for media messages)
        async with self.session.begin_nested():
            # Ensure sender exists and is committed
            sender = await self.session.get(Sender, message.sender_jid)
            if sender is None:
                sender = Sender(
                    **BaseSender(
                        jid=message.sender_jid,  # Use normalized JID from message
                        push_name=sender_pushname,
                    ).model_dump()
                )
                await self.upsert(sender)
                await (
                    self.session.flush()
                )  # Ensure sender is visible in this transaction

            if message.group_jid:
                group = await self.session.get(Group, message.group_jid)
                if group is None:
                    group = Group(**BaseGroup(group_jid=message.group_jid).model_dump())
                    await self.upsert(group)
                    await self.session.flush()

            # Finally add the message
            return await self.upsert(message)

    async def upsert(self, model):
        return await upsert(self.session, model)
