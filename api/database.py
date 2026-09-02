import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from api.config import settings

logger = logging.getLogger(__name__)

db_url = settings.sqlalchemy_database_url

# Serverless connection settings
connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,
}

if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    engine_kwargs.update({
        "pool_size": 5,
        "max_overflow": 10,
        "pool_recycle": 300,
    })

engine = create_engine(
    db_url,
    connect_args=connect_args,
    **engine_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db() -> None:
    """
    Crea las tablas automáticamente si no existen (idempotente).
    Garantiza la persistencia aunque no se haya ejecutado scripts/setup_db.py.
    ADVERTENCIA: SQLite no es viable en Vercel (filesystem efímero / solo lectura);
    en ese entorno se debe configurar POSTGRES_URL/DATABASE_URL con PostgreSQL.
    """
    if db_url.startswith("sqlite") and os.getenv("VERCEL"):
        logger.error(
            "DATABASE_URL apunta a SQLite dentro de Vercel. El filesystem serverless "
            "es efímero/solo-lectura: los datos NO van a persistir entre invocaciones. "
            "Configurá POSTGRES_URL o DATABASE_URL con PostgreSQL (Vercel Postgres / Neon / Supabase)."
        )
    try:
        import api.models  # noqa: F401  (registra los modelos en Base.metadata)
        Base.metadata.create_all(bind=engine)
        logger.info("Esquema de base de datos verificado/creado correctamente.")
    except Exception as e:
        logger.error(f"No se pudieron crear/verificar las tablas en la base de datos: {e}")

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
