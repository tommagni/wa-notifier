from copy import deepcopy
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    global settings
    # Create and configure logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(settings.log_level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(UTCKeyValueFormatter(LOG_FORMAT, LOG_DATE_FORMAT))
    root_logger.addHandler(handler)

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
    from uvicorn.config import LOGGING_CONFIG

    print(f"Running on {settings.host}:{settings.port}")

    uvicorn_log_config = deepcopy(LOGGING_CONFIG)
    uvicorn_log_config["handlers"]["default"]["stream"] = "ext://sys.stdout"
    uvicorn_log_config["handlers"]["access"]["stream"] = "ext://sys.stdout"
    uvicorn_log_config["formatters"]["default"] = {
        "class": "utils.log_formatter.UTCKeyValueFormatter",
        "format": LOG_FORMAT,
        "datefmt": LOG_DATE_FORMAT,
    }
    uvicorn_log_config["formatters"]["access"] = {
        "class": "utils.log_formatter.UTCKeyValueFormatter",
        "format": LOG_FORMAT,
        "datefmt": LOG_DATE_FORMAT,
    }

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_config=uvicorn_log_config,
    )
