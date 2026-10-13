import platform
import sqlalchemy
from fastapi import APIRouter
from sqlalchemy import text
from datetime import datetime, timezone
from api.config import settings
from api.database import engine, SessionLocal

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
def health_check():
    # This endpoint NEVER depends on DB dependency injection: if the engine
    # could not be initialized (invalid URL/driver) it still answers 200 with
    # the diagnosis, so that a curl to /api/health is enough to see what is
    # going on without digging through Vercel logs.
    db_status = "connected"
    if engine is None:
        db_status = "unavailable: engine not initialized (check DATABASE_URL/POSTGRES_URL and startup logs)"
    else:
        try:
            db = SessionLocal()
            try:
                db.execute(text("SELECT 1"))
            finally:
                db.close()
        except Exception as e:
            db_status = f"unreachable: {str(e)}"

    return {
        # Immediate visibility of the deployed build: one curl to /api/health
        # shows which versions Vercel vendored, without digging through logs.
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "environment": settings.ENVIRONMENT,
        "python": platform.python_version(),
        "sqlalchemy": sqlalchemy.__version__,
        "db_driver": engine.url.get_driver_name() if engine is not None else None,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
