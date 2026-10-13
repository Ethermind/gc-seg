import logging
import os
from fastapi import HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
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
elif db_url.startswith("postgresql"):
    connect_args["connect_timeout"] = 10
    engine_kwargs.update({
        "pool_size": 5,
        "max_overflow": 10,
        "pool_recycle": 300,
    })

# El engine se crea al importar el módulo (cold start serverless). Si la URL o el
# driver DBAPI tienen un problema, NUNCA debe morir el import: eso convertiría un
# error puntual de configuración en un FUNCTION_INVOCATION_FAILED que tira abajo
# TODOS los endpoints. En su lugar degradamos: init_db/get_db loguean y las rutas
# responden 500 JSON entendible, y queda un log claro con la acción correctiva.
try:
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        **engine_kwargs
    )
except Exception as e:
    logger.error(
        "No se pudo inicializar el engine de base de datos. "
        "Verificar el esquema de DATABASE_URL/POSTGRES_URL (se espera postgres:// o postgresql://, "
        "sin sufijos de driver tipo +psycopg) y que el driver psycopg v3 esté instalado. "
        f"URL efectiva: {db_url.split('@')[-1] if '@' in db_url else db_url.split(':')[0] + '://***'} | Error: {e}"
    )
    engine = None

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db() -> None:
    """
    Crea las tablas automáticamente si no existen (idempotente).
    Garantiza la persistencia aunque no se haya ejecutado scripts/setup_db.py.
    ADVERTENCIA: SQLite no es viable en Vercel (filesystem efímero / solo lectura);
    en ese entorno se debe configurar POSTGRES_URL/DATABASE_URL con PostgreSQL.
    """
    if engine is None:
        logger.error("init_db omitido: el engine de base de datos no se pudo inicializar (ver log previo).")
        return
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
    if engine is None:
        # 503 JSON limpio (no RuntimeError): FastAPI lo convierte en
        # {"detail": ...} sin tumbar el worker.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La base de datos no está disponible en este momento. Error de configuración de conexión."
        )
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
