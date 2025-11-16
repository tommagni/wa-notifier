from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from strawberry.fastapi import GraphQLRouter

from .schema import schema, Context
from .deps import get_db_async_session


async def get_context(
    session: Annotated[AsyncSession, Depends(get_db_async_session)],
) -> Context:
    """Get GraphQL context with database session."""
    return Context(session)


# Create the Strawberry GraphQL router with GraphiQL enabled
graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context,
    graphiql=True,
    path="/graphql",
)


def create_graphql_router() -> GraphQLRouter:
    """Create and return the GraphQL router."""
    return graphql_app
