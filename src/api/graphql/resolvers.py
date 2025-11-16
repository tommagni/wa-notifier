from typing import List, Optional
from datetime import datetime
from sqlmodel import select, and_, or_, func
from sqlmodel.ext.asyncio.session import AsyncSession
import strawberry

from .types import Message, Group, Sender, MessageFilter, GroupFilter, SenderFilter, PaginationInput
from models import Message as DBMessage, Group as DBGroup, Sender as DBSender


async def get_messages(
    session: AsyncSession,
    filter_input: Optional[MessageFilter] = None,
    pagination: Optional[PaginationInput] = None,
) -> List[Message]:
    """Get messages with optional filtering and pagination."""
    query = select(DBMessage)

    # Apply filters
    if filter_input:
        conditions = []
        if filter_input.sender_jid:
            conditions.append(DBMessage.sender_jid == filter_input.sender_jid)
        if filter_input.group_jid:
            conditions.append(DBMessage.group_jid == filter_input.group_jid)
        if filter_input.is_relevant is not None:
            conditions.append(DBMessage.is_relevant == filter_input.is_relevant)
        if filter_input.has_text is not None:
            if filter_input.has_text:
                conditions.append(DBMessage.text.isnot(None))
            else:
                conditions.append(DBMessage.text.is_(None))
        if filter_input.start_date:
            conditions.append(DBMessage.timestamp >= filter_input.start_date)
        if filter_input.end_date:
            conditions.append(DBMessage.timestamp <= filter_input.end_date)

        if conditions:
            query = query.where(and_(*conditions))

    # Apply pagination
    if pagination:
        if pagination.offset:
            query = query.offset(pagination.offset)
        if pagination.limit:
            query = query.limit(pagination.limit)

    # Order by timestamp descending (newest first)
    query = query.order_by(DBMessage.timestamp.desc())

    result = await session.exec(query)
    db_messages = result.all()

    # Convert to GraphQL types
    messages = []
    for db_msg in db_messages:
        message = Message(
            message_id=db_msg.message_id,
            timestamp=db_msg.timestamp,
            text=db_msg.text,
            media_url=db_msg.media_url,
            chat_jid=db_msg.chat_jid,
            sender_jid=db_msg.sender_jid,
            group_jid=db_msg.group_jid,
            reply_to_id=db_msg.reply_to_id,
            is_relevant=db_msg.is_relevant,
            reasoning=db_msg.reasoning,
            relevancy_total_token_count=db_msg.relevancy_total_token_count,
            relevancy_input_tokens=db_msg.relevancy_input_tokens,
            relevancy_output_tokens=db_msg.relevancy_output_tokens,
        )
        messages.append(message)

    return messages


async def get_message_count(
    session: AsyncSession,
    filter_input: Optional[MessageFilter] = None,
) -> int:
    """Get total count of messages with optional filtering."""
    query = select(func.count(DBMessage.message_id))

    # Apply filters
    if filter_input:
        conditions = []
        if filter_input.sender_jid:
            conditions.append(DBMessage.sender_jid == filter_input.sender_jid)
        if filter_input.group_jid:
            conditions.append(DBMessage.group_jid == filter_input.group_jid)
        if filter_input.is_relevant is not None:
            conditions.append(DBMessage.is_relevant == filter_input.is_relevant)
        if filter_input.has_text is not None:
            if filter_input.has_text:
                conditions.append(DBMessage.text.isnot(None))
            else:
                conditions.append(DBMessage.text.is_(None))
        if filter_input.start_date:
            conditions.append(DBMessage.timestamp >= filter_input.start_date)
        if filter_input.end_date:
            conditions.append(DBMessage.timestamp <= filter_input.end_date)

        if conditions:
            query = query.where(and_(*conditions))

    result = await session.exec(query)
    return result.one()


async def get_groups(
    session: AsyncSession,
    filter_input: Optional[GroupFilter] = None,
    pagination: Optional[PaginationInput] = None,
) -> List[Group]:
    """Get groups with optional filtering and pagination."""
    query = select(DBGroup)

    # Apply filters
    if filter_input:
        conditions = []
        if filter_input.managed is not None:
            conditions.append(DBGroup.managed == filter_input.managed)
        if filter_input.notify_on_spam is not None:
            conditions.append(DBGroup.notify_on_spam == filter_input.notify_on_spam)
        if filter_input.has_community_keys is not None:
            if filter_input.has_community_keys:
                conditions.append(DBGroup.community_keys.isnot(None))
            else:
                conditions.append(DBGroup.community_keys.is_(None))

        if conditions:
            query = query.where(and_(*conditions))

    # Apply pagination
    if pagination:
        if pagination.offset:
            query = query.offset(pagination.offset)
        if pagination.limit:
            query = query.limit(pagination.limit)

    # Order by last_ingest descending
    query = query.order_by(DBGroup.last_ingest.desc())

    result = await session.exec(query)
    db_groups = result.all()

    # Convert to GraphQL types
    groups = []
    for db_group in db_groups:
        group = Group(
            group_jid=db_group.group_jid,
            group_name=db_group.group_name,
            group_topic=db_group.group_topic,
            owner_jid=db_group.owner_jid,
            managed=db_group.managed,
            forward_url=db_group.forward_url,
            notify_on_spam=db_group.notify_on_spam,
            community_keys=db_group.community_keys,
            last_ingest=db_group.last_ingest,
            last_summary_sync=db_group.last_summary_sync,
        )
        groups.append(group)

    return groups


async def get_group_count(
    session: AsyncSession,
    filter_input: Optional[GroupFilter] = None,
) -> int:
    """Get total count of groups with optional filtering."""
    query = select(func.count(DBGroup.group_jid))

    # Apply filters
    if filter_input:
        conditions = []
        if filter_input.managed is not None:
            conditions.append(DBGroup.managed == filter_input.managed)
        if filter_input.notify_on_spam is not None:
            conditions.append(DBGroup.notify_on_spam == filter_input.notify_on_spam)
        if filter_input.has_community_keys is not None:
            if filter_input.has_community_keys:
                conditions.append(DBGroup.community_keys.isnot(None))
            else:
                conditions.append(DBGroup.community_keys.is_(None))

        if conditions:
            query = query.where(and_(*conditions))

    result = await session.exec(query)
    return result.one()


async def get_senders(
    session: AsyncSession,
    filter_input: Optional[SenderFilter] = None,
    pagination: Optional[PaginationInput] = None,
) -> List[Sender]:
    """Get senders with optional filtering and pagination."""
    query = select(DBSender)

    # Apply filters
    if filter_input:
        conditions = []
        if filter_input.has_push_name is not None:
            if filter_input.has_push_name:
                conditions.append(DBSender.push_name.isnot(None))
            else:
                conditions.append(DBSender.push_name.is_(None))

        if conditions:
            query = query.where(and_(*conditions))

    # Apply pagination
    if pagination:
        if pagination.offset:
            query = query.offset(pagination.offset)
        if pagination.limit:
            query = query.limit(pagination.limit)

    result = await session.exec(query)
    db_senders = result.all()

    # Convert to GraphQL types
    senders = []
    for db_sender in db_senders:
        sender = Sender(
            jid=db_sender.jid,
            push_name=db_sender.push_name,
        )
        senders.append(sender)

    return senders


async def get_sender_count(
    session: AsyncSession,
    filter_input: Optional[SenderFilter] = None,
) -> int:
    """Get total count of senders with optional filtering."""
    query = select(func.count(DBSender.jid))

    # Apply filters
    if filter_input:
        conditions = []
        if filter_input.has_push_name is not None:
            if filter_input.has_push_name:
                conditions.append(DBSender.push_name.isnot(None))
            else:
                conditions.append(DBSender.push_name.is_(None))

        if conditions:
            query = query.where(and_(*conditions))

    result = await session.exec(query)
    return result.one()


async def get_message_by_id(session: AsyncSession, message_id: str) -> Optional[Message]:
    """Get a single message by ID."""
    query = select(DBMessage).where(DBMessage.message_id == message_id)
    result = await session.exec(query)
    db_message = result.first()

    if not db_message:
        return None

    return Message(
        message_id=db_message.message_id,
        timestamp=db_message.timestamp,
        text=db_message.text,
        media_url=db_message.media_url,
        chat_jid=db_message.chat_jid,
        sender_jid=db_message.sender_jid,
        group_jid=db_message.group_jid,
        reply_to_id=db_message.reply_to_id,
        is_relevant=db_message.is_relevant,
        reasoning=db_message.reasoning,
        relevancy_total_token_count=db_message.relevancy_total_token_count,
        relevancy_input_tokens=db_message.relevancy_input_tokens,
        relevancy_output_tokens=db_message.relevancy_output_tokens,
    )


async def get_group_by_jid(session: AsyncSession, group_jid: str) -> Optional[Group]:
    """Get a single group by JID."""
    query = select(DBGroup).where(DBGroup.group_jid == group_jid)
    result = await session.exec(query)
    db_group = result.first()

    if not db_group:
        return None

    return Group(
        group_jid=db_group.group_jid,
        group_name=db_group.group_name,
        group_topic=db_group.group_topic,
        owner_jid=db_group.owner_jid,
        managed=db_group.managed,
        forward_url=db_group.forward_url,
        notify_on_spam=db_group.notify_on_spam,
        community_keys=db_group.community_keys,
        last_ingest=db_group.last_ingest,
        last_summary_sync=db_group.last_summary_sync,
    )


async def get_sender_by_jid(session: AsyncSession, jid: str) -> Optional[Sender]:
    """Get a single sender by JID."""
    query = select(DBSender).where(DBSender.jid == jid)
    result = await session.exec(query)
    db_sender = result.first()

    if not db_sender:
        return None

    return Sender(
        jid=db_sender.jid,
        push_name=db_sender.push_name,
    )
