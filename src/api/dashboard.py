import logging
from datetime import datetime
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from .deps import get_db_async_session
from models import Message, Sender, Group

logger = logging.getLogger(__name__)


class MessageResponse(BaseModel):
    """Response model for message data in dashboard."""
    message_id: str
    timestamp: datetime
    text: Optional[str] = None
    media_url: Optional[str] = None
    chat_jid: str
    sender_jid: str
    group_jid: Optional[str] = None
    reply_to_id: Optional[str] = None
    is_relevant: Optional[bool] = None
    reasoning: Optional[str] = None
    relevancy_total_token_count: Optional[int] = None
    relevancy_input_tokens: Optional[int] = None
    relevancy_output_tokens: Optional[int] = None
    sender_name: Optional[str] = None
    group_name: Optional[str] = None


class MessageStatsResponse(BaseModel):
    """Response model for message statistics."""
    total_messages: int
    relevant_messages: int
    irrelevant_messages: int
    pending_analysis: int
    avg_tokens_per_message: Optional[float] = None


class PaginatedMessagesResponse(BaseModel):
    """Response model for paginated message list."""
    messages: List[MessageResponse]
    total_count: int
    page: int
    page_size: int
    has_more: bool


router = APIRouter(tags=["dashboard"])


@router.get("/messages/stats", response_model=MessageStatsResponse)
async def get_message_stats(
    session: Annotated[AsyncSession, Depends(get_db_async_session)],
) -> MessageStatsResponse:
    """
    Get statistics about messages and their relevancy analysis.
    """
    # Count total messages
    total_query = select(func.count(Message.message_id))
    total_result = await session.exec(total_query)
    total_messages = total_result.one()

    # Count relevant messages
    relevant_query = select(func.count(Message.message_id)).where(Message.is_relevant.is_(True))
    relevant_result = await session.exec(relevant_query)
    relevant_messages = relevant_result.one()

    # Count irrelevant messages
    irrelevant_query = select(func.count(Message.message_id)).where(Message.is_relevant.is_(False))
    irrelevant_result = await session.exec(irrelevant_query)
    irrelevant_messages = irrelevant_result.one()

    # Count pending analysis (null is_relevant)
    pending_query = select(func.count(Message.message_id)).where(Message.is_relevant.is_(None))
    pending_result = await session.exec(pending_query)
    pending_analysis = pending_result.one()

    # Calculate average tokens per message (only for analyzed messages)
    avg_tokens_query = select(func.avg(Message.relevancy_total_token_count)).where(
        Message.relevancy_total_token_count.isnot(None)
    )
    avg_tokens_result = await session.exec(avg_tokens_query)
    avg_tokens = avg_tokens_result.one()

    return MessageStatsResponse(
        total_messages=total_messages,
        relevant_messages=relevant_messages,
        irrelevant_messages=irrelevant_messages,
        pending_analysis=pending_analysis,
        avg_tokens_per_message=avg_tokens,
    )


@router.get("/messages", response_model=PaginatedMessagesResponse)
async def get_messages(
    session: Annotated[AsyncSession, Depends(get_db_async_session)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Number of messages per page"),
    relevance_filter: Optional[str] = Query(None, description="Filter by relevance: 'relevant', 'irrelevant', or 'pending'"),
    group_jid: Optional[str] = Query(None, description="Filter by group JID"),
    search_text: Optional[str] = Query(None, description="Search in message text"),
) -> PaginatedMessagesResponse:
    """
    Get paginated list of messages with relevancy information.

    - **page**: Page number (starts from 1)
    - **page_size**: Number of messages per page (1-100)
    - **relevance_filter**: Filter by relevance status ('relevant', 'irrelevant', 'pending')
    - **group_jid**: Filter by specific group
    - **search_text**: Search within message text (case-insensitive)
    """
    # Build base query with joins to get sender and group names
    query = (
        select(
            Message.message_id,
            Message.timestamp,
            Message.text,
            Message.media_url,
            Message.chat_jid,
            Message.sender_jid,
            Message.group_jid,
            Message.reply_to_id,
            Message.is_relevant,
            Message.reasoning,
            Message.relevancy_total_token_count,
            Message.relevancy_input_tokens,
            Message.relevancy_output_tokens,
            Sender.push_name.label("sender_name"),
            Group.group_name.label("group_name"),
        )
        .join(Sender, Message.sender_jid == Sender.jid, isouter=True)
        .join(Group, Message.group_jid == Group.group_jid, isouter=True)
    )

    # Apply relevance filter
    if relevance_filter == "relevant":
        query = query.where(Message.is_relevant.is_(True))
    elif relevance_filter == "irrelevant":
        query = query.where(Message.is_relevant.is_(False))
    elif relevance_filter == "pending":
        query = query.where(Message.is_relevant.is_(None))

    # Apply group filter
    if group_jid:
        query = query.where(Message.group_jid == group_jid)

    # Apply text search
    if search_text:
        query = query.where(Message.text.ilike(f"%{search_text}%"))

    # Get total count for pagination
    count_query = query.with_only_columns(func.count(Message.message_id))
    count_result = await session.exec(count_query)
    total_count = count_result.one()

    # Apply ordering and pagination
    query = query.order_by(Message.timestamp.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = await session.exec(query)
    rows = result.all()

    # Convert to response models
    messages = []
    for row in rows:
        messages.append(MessageResponse(
            message_id=row.message_id,
            timestamp=row.timestamp,
            text=row.text,
            media_url=row.media_url,
            chat_jid=row.chat_jid,
            sender_jid=row.sender_jid,
            group_jid=row.group_jid,
            reply_to_id=row.reply_to_id,
            is_relevant=row.is_relevant,
            reasoning=row.reasoning,
            relevancy_total_token_count=row.relevancy_total_token_count,
            relevancy_input_tokens=row.relevancy_input_tokens,
            relevancy_output_tokens=row.relevancy_output_tokens,
            sender_name=row.sender_name,
            group_name=row.group_name,
        ))

    has_more = (page * page_size) < total_count

    return PaginatedMessagesResponse(
        messages=messages,
        total_count=total_count,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )
