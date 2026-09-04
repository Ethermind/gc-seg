from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from api.config import settings
from api.database import init_db
from api.routes import contact, reviews, health, admin, auth

app = FastAPI(
    title="Giaconi-Capra® PAS — Backend API",
    description="API Serverless para gestión de cotizaciones, leads, testimonios, autenticación y administración",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Crear/verificar tablas al arrancar (idempotente). Crucial en serverless,
# donde los cold starts no ejecutan scripts/setup_db.py.
init_db()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router con prefijo /api
api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(contact.router)
api_router.include_router(reviews.router)
api_router.include_router(health.router)
api_router.include_router(admin.router)

app.include_router(api_router)

# Soporte directo sin prefijo /api (por si Vercel remueve el prefijo en el rewrite)
app.include_router(auth.router)
app.include_router(contact.router)
app.include_router(reviews.router)
app.include_router(health.router)
app.include_router(admin.router)

@app.get("/")
def root_status():
    return {
        "service": "Giaconi-Capra® PAS API",
        "status": "online",
        "docs": "/api/docs"
    }

# Config pública para el frontend: mantiene frontend y backend consistentes
# (misma site key de Turnstile en ambos lados -> los envíos no fallan por desajuste)
@app.get("/api/config")
@app.get("/config")
def public_config():
    # Devuelve null si no hay clave: el frontend cae a la site key de prueba de Cloudflare
    return {
        "turnstile_site_key": settings.TURNSTILE_SITE_KEY or None,
        "environment": settings.ENVIRONMENT,
    }
