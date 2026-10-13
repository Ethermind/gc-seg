import logging
from fastapi import HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from api.config import settings

logger = logging.getLogger(__name__)

db_url = settings.sqlalchemy_database_url


def _is_supported_url(url: str) -> bool:
    """This project is PostgreSQL-only (local and production).

    SQLite is not supported in ANY environment: local dev, tests and
    production all run PostgreSQL (driver psycopg v3).
    """
    return url.startswith("postgresql")


# The engine is created at module import time (serverless cold start). If the
# URL or the DBAPI driver has a problem, the import must NEVER die: that would
# turn a single configuration error into a FUNCTION_INVOCATION_FAILED taking
# down ALL endpoints. Instead we degrade gracefully: init_db/get_db log clearly
# and the routes answer an understandable JSON error.
engine = None
if not _is_supported_url(db_url):
    logger.error(
        "Unsupported database URL scheme. This project requires PostgreSQL: "
        "set POSTGRES_URL/DATABASE_URL to postgresql://... (legacy postgres:// "
        "is normalized automatically). "
        f"Effective URL: {db_url.split('@')[-1] if '@' in db_url else db_url.split(':')[0] + '://***'}"
    )
else:
    try:
        engine = create_engine(
            db_url,
            connect_args={"connect_timeout": 10},
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_recycle=300,
        )
    except Exception as e:
        logger.error(
            "Could not initialize the database engine. Check the DATABASE_URL/POSTGRES_URL "
            "scheme (expected postgres:// or postgresql://, without driver suffixes like "
            "+psycopg) and that the psycopg v3 driver is installed. "
            f"Effective URL: {db_url.split('@')[-1] if '@' in db_url else db_url.split(':')[0] + '://***'} | Error: {e}"
        )
        engine = None

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db() -> None:
    """
    Creates tables automatically if they do not exist (idempotent).
    Guarantees persistence even when scripts/setup_db.py was never run.
    """
    if engine is None:
        logger.error("init_db skipped: the database engine could not be initialized (see previous log).")
        return
    try:
        import api.models  # noqa: F401  (registers models in Base.metadata)
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema verified/created successfully.")
    except Exception as e:
        logger.error(f"Could not create/verify database tables: {e}")

def get_db():
    if engine is None:
        # Clean JSON 503 (not a bare RuntimeError): FastAPI converts it to
        # {"detail": ...} without killing the worker.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The database is not available at the moment. Connection configuration error."
        )
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
