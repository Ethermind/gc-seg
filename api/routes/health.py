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
    # Este endpoint NUNCA depende de la DI de la DB: si el engine no se pudo
    # inicializar (URL/driver inválido) igual responde 200 con el diagnóstico,
    # para que un curl a /api/health alcance para ver qué está pasando
    # sin excavar en los logs de Vercel.
    db_status = "connected"
    if engine is None:
        db_status = "unavailable: engine no inicializado (revisar DATABASE_URL/POSTGRES_URL y logs de arranque)"
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
        # Visibilidad inmediata del build desplegado: un curl a /api/health muestra
        # qué versiones vendoró Vercel, sin tener que excavar en los logs.
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "environment": settings.ENVIRONMENT,
        "python": platform.python_version(),
        "sqlalchemy": sqlalchemy.__version__,
        "db_driver": engine.url.get_driver_name() if engine is not None else None,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
