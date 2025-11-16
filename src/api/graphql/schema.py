from typing import List, Optional
import strawberry
from strawberry.types import Info
from strawberry.fastapi import BaseContext
from sqlmodel.ext.asyncio.session import AsyncSession

from .types import (
    Message,
    Group,
    Sender,
    MessageFilter,
    GroupFilter,
    SenderFilter,
    PaginationInput,
)
from .resolvers import (
    get_messages,
    get_message_count,
    get_groups,
    get_group_count,
    get_senders,
    get_sender_count,
    get_message_by_id,
    get_group_by_jid,
    get_sender_by_jid,
)


class Context(BaseContext):
    """GraphQL context that provides access to database session."""
    def __init__(self, session: AsyncSession):
        super().__init__()
        self.session = session


@strawberry.type
class Query:
    @strawberry.field
    async def messages(
        self,
        info: Info,
        filter: Optional[MessageFilter] = None,
        pagination: Optional[PaginationInput] = None,
    ) -> List[Message]:
        """Get messages with optional filtering and pagination."""
        return await get_messages(info.context.session, filter, pagination)

    @strawberry.field
    async def message_count(
        self,
        info: Info,
        filter: Optional[MessageFilter] = None,
    ) -> int:
        """Get total count of messages with optional filtering."""
        return await get_message_count(info.context.session, filter)

    @strawberry.field
    async def message(self, info: Info, message_id: str) -> Optional[Message]:
        """Get a single message by ID."""
        return await get_message_by_id(info.context.session, message_id)

    @strawberry.field
    async def groups(
        self,
        info: Info,
        filter: Optional[GroupFilter] = None,
        pagination: Optional[PaginationInput] = None,
    ) -> List[Group]:
        """Get groups with optional filtering and pagination."""
        return await get_groups(info.context.session, filter, pagination)

    @strawberry.field
    async def group_count(
        self,
        info: Info,
        filter: Optional[GroupFilter] = None,
    ) -> int:
        """Get total count of groups with optional filtering."""
        return await get_group_count(info.context.session, filter)

    @strawberry.field
    async def group(self, info: Info, group_jid: str) -> Optional[Group]:
        """Get a single group by JID."""
        return await get_group_by_jid(info.context.session, group_jid)

    @strawberry.field
    async def senders(
        self,
        info: Info,
        filter: Optional[SenderFilter] = None,
        pagination: Optional[PaginationInput] = None,
    ) -> List[Sender]:
        """Get senders with optional filtering and pagination."""
        return await get_senders(info.context.session, filter, pagination)

    @strawberry.field
    async def sender_count(
        self,
        info: Info,
        filter: Optional[SenderFilter] = None,
    ) -> int:
        """Get total count of senders with optional filtering."""
        return await get_sender_count(info.context.session, filter)

    @strawberry.field
    async def sender(self, info: Info, jid: str) -> Optional[Sender]:
        """Get a single sender by JID."""
        return await get_sender_by_jid(info.context.session, jid)


# Create the GraphQL schema
schema = strawberry.Schema(Query)
