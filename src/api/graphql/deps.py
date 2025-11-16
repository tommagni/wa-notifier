from typing import Annotated

from fastapi import Depends, Request
from sqlmodel.ext.asyncio.session import AsyncSession


async def get_db_async_session(request: Request) -> AsyncSession:
    """Get database session from request app state."""
    assert request.app.state.async_session, "AsyncSession generator not initialized"
    async with request.app.state.async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
