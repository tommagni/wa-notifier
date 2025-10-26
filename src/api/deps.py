from typing import Annotated

from fastapi import Depends, Request
from sqlmodel.ext.asyncio.session import AsyncSession

from config import Settings
from handler import MessageHandler


async def get_db_async_session(request: Request) -> AsyncSession:
    assert request.app.state.async_session, "AsyncSession generator not initialized"
    async with request.app.state.async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_handler(
    session: Annotated[AsyncSession, Depends(get_db_async_session)],
    request: Request,
) -> MessageHandler:
    settings: Settings = request.app.state.settings
    return MessageHandler(session, settings)
