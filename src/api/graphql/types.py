from datetime import datetime
from typing import List, Optional
import strawberry
from strawberry import auto


@strawberry.type
class Sender:
    jid: str
    push_name: Optional[str]


@strawberry.type
class Group:
    group_jid: str
    group_name: Optional[str]
    group_topic: Optional[str]
    owner_jid: Optional[str]
    managed: bool
    forward_url: Optional[str]
    notify_on_spam: bool
    community_keys: Optional[List[str]]
    last_ingest: datetime
    last_summary_sync: datetime

    # Relationships will be resolved by resolvers
    @strawberry.field
    async def owner(self) -> Optional[Sender]:
        # This will be resolved by the resolver
        return None

    @strawberry.field
    async def messages(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
        is_relevant: Optional[bool] = None,
    ) -> List["Message"]:
        # This will be resolved by the resolver
        return []


@strawberry.type
class Message:
    message_id: str
    timestamp: datetime
    text: Optional[str]
    media_url: Optional[str]
    chat_jid: str
    sender_jid: str
    group_jid: Optional[str]
    reply_to_id: Optional[str]
    is_relevant: Optional[bool]
    reasoning: Optional[str]
    relevancy_total_token_count: Optional[int]
    relevancy_input_tokens: Optional[int]
    relevancy_output_tokens: Optional[int]

    # Relationships will be resolved by resolvers
    @strawberry.field
    async def sender(self) -> Optional[Sender]:
        # This will be resolved by the resolver
        return None

    @strawberry.field
    async def group(self) -> Optional[Group]:
        # This will be resolved by the resolver
        return None

    @strawberry.field
    async def replies(self, limit: Optional[int] = None, offset: Optional[int] = 0) -> List["Message"]:
        # This will be resolved by the resolver
        return []


# Input types for filtering
@strawberry.input
class MessageFilter:
    sender_jid: Optional[str] = None
    group_jid: Optional[str] = None
    is_relevant: Optional[bool] = None
    has_text: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@strawberry.input
class GroupFilter:
    managed: Optional[bool] = None
    notify_on_spam: Optional[bool] = None
    has_community_keys: Optional[bool] = None


@strawberry.input
class SenderFilter:
    has_push_name: Optional[bool] = None


# Pagination input
@strawberry.input
class PaginationInput:
    limit: Optional[int] = 50
    offset: Optional[int] = 0
