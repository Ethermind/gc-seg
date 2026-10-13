from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from api.config import settings
from api.database import init_db
from api.ratelimit import limiter
from api.routes import contact, reviews, health, admin, auth, manuals, coverages, faqs

app = FastAPI(
    title="Giaconi-Capra® PAS — Backend API",
    description="Serverless API for quote management, leads, testimonials, authentication and administration",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Create/verify tables on startup (idempotent). Crucial in serverless,
# where cold starts do not run scripts/setup_db.py.
init_db()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Router with /api prefix
api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(contact.router)
api_router.include_router(reviews.router)
api_router.include_router(health.router)
api_router.include_router(admin.router)
api_router.include_router(manuals.router)
api_router.include_router(coverages.router)
api_router.include_router(faqs.router)

app.include_router(api_router)

# Direct support without the /api prefix (in case Vercel strips it in the rewrite)
app.include_router(auth.router)
app.include_router(contact.router)
app.include_router(reviews.router)
app.include_router(health.router)
app.include_router(admin.router)
app.include_router(manuals.router)
app.include_router(coverages.router)
app.include_router(faqs.router)

@app.get("/")
def root_status():
    return {
        "service": "Giaconi-Capra® PAS API",
        "status": "online",
        "docs": "/api/docs"
    }

# Public config for the frontend: keeps frontend and backend consistent
# (same Turnstile site key on both sides -> submissions do not fail on mismatch)
@app.get("/api/config")
@app.get("/config")
def public_config():
    # Returns null when no key is set: the frontend falls back to Cloudflare's test site key
    return {
        "turnstile_site_key": settings.TURNSTILE_SITE_KEY or None,
        "environment": settings.ENVIRONMENT,
    }
