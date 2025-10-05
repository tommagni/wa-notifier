import time
from typing import Annotated, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import text

from .deps import get_db_async_session

router = APIRouter()


@router.get("/readiness")
async def readiness() -> Dict[str, str]:
    """Simple readiness check that returns immediately."""
    return {"status": "ok"}


@router.get("/status")
async def status(
    session: Annotated[AsyncSession, Depends(get_db_async_session)],
) -> Dict[str, Any]:
    """
    Health check that verifies database connection.

    Returns 200 if database check passes, otherwise returns appropriate error status.
    """
    health_data = {"status": "healthy", "checks": {}, "timestamp": time.time()}

    # Track overall health status
    overall_healthy = True
    error_messages = []

    # Check: Database connectivity
    db_start_time = time.time()
    try:
        # Execute a simple test query to verify database connectivity
        # Use connection() to get underlying SQLAlchemy connection for raw SQL
        conn = await session.connection()
        raw_result = await conn.execute(text("SELECT 1 + 1 as test_result"))
        test_value = raw_result.fetchone()
        db_duration = time.time() - db_start_time

        # Verify the query returned expected result
        if test_value and test_value[0] == 2:
            health_data["checks"]["database"] = {
                "status": "healthy",
                "duration_seconds": db_duration,
            }
        else:
            overall_healthy = False
            error_messages.append("Database query returned unexpected result")
            health_data["checks"]["database"] = {
                "status": "unhealthy",
                "error": "Query result validation failed",
                "duration_seconds": db_duration,
            }

    except Exception as e:
        db_duration = time.time() - db_start_time
        overall_healthy = False
        error_messages.append(f"Database connectivity check failed: {str(e)}")
        health_data["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
            "duration_seconds": db_duration,
        }

    # Calculate total duration
    health_data["total_duration_seconds"] = time.time() - health_data["timestamp"]

    # Return appropriate response based on health status
    if overall_healthy:
        return health_data
    else:
        # Update status to indicate issues
        health_data["status"] = "unhealthy"
        health_data["errors"] = error_messages

        # Return 503 Service Unavailable for health check failures
        raise HTTPException(status_code=503, detail=health_data)
