from contextlib import asynccontextmanager
import sys
from warnings import warn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
import logging

from api import status, webhook
from api.graphql import create_graphql_router
import models  # noqa
from config import Settings
from utils.log_formatter import LOG_DATE_FORMAT, LOG_FORMAT, UTCKeyValueFormatter

settings = Settings()  # pyright: ignore [reportCallIssue]


def configure_logging(log_level: str) -> None:
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(UTCKeyValueFormatter(LOG_FORMAT, LOG_DATE_FORMAT))
    root_logger.addHandler(handler)

    # Ensure Uvicorn loggers propagate to the root handler and don't keep
    # their own default formatter/handlers.
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    global settings
    configure_logging(settings.log_level)

    app.state.settings = settings

    if settings.db_uri.startswith("postgresql://"):
        warn("use 'postgresql+asyncpg://' instead of 'postgresql://' in db_uri")
    engine = create_async_engine(
        settings.db_uri,
        pool_size=20,
        max_overflow=40,
        pool_timeout=30,
        pool_pre_ping=True,
        pool_recycle=600,
        future=True,
    )
    async_session = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    app.state.db_engine = engine
    app.state.async_session = async_session
    try:
        yield
    finally:
        await engine.dispose()


# Initialize FastAPI app
app = FastAPI(title="WhatsApp Message Reader", lifespan=lifespan)

# Configure CORS
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:8000",
]
if settings.host_ip_address:
    allowed_origins.append(f"http://{settings.host_ip_address}:8000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook.router)
app.include_router(status.router)

# Include GraphQL router (handles both /graphql endpoint and GraphiQL UI)
graphql_app = create_graphql_router()
app.include_router(graphql_app, prefix="")

if __name__ == "__main__":
    import uvicorn

    configure_logging(settings.log_level)
    print(f"Running on {settings.host}:{settings.port}")

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_config=None,
    )
