from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from api.config import settings
from api.routes import contact, reviews, health, admin, auth

app = FastAPI(
    title="Giaconi-Capra® PAS — Backend API",
    description="API Serverless para gestión de cotizaciones, leads, testimonios, autenticación y administración",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

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
