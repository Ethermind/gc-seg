import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List, Optional
from dotenv import load_dotenv

# Cargar .env.local (generado por Vercel CLI) y .env
load_dotenv(".env.local")
load_dotenv(".env")


def _find_project_root() -> Path:
    """
    Resuelve la raíz real del proyecto (el directorio donde vive este repo),
    sin importar el CWD del proceso ni si el código se ejecuta desde una
    copia cacheada (vercel dev copia el código a .vercel/cache/index_py/,
    que está gitignored e identificable por el componente ".vercel").
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        # Descartar copias internas del CLI de Vercel (p. ej. .vercel/cache/...)
        if ".vercel" in parent.parts:
            continue
        # La raíz del repo contiene .git (los bundles de Vercel no lo copian)
        if (parent / ".git").exists() and parent.name != "index_py":
            return parent
    # Fallback: la raíz del paquete del proyecto tal como se desplegó
    return here.parent.parent


def _resolve_sqlite_path(rel_path: str) -> str:
    """Ancla rutas SQLite relativas a la raíz del proyecto (CWD-independiente)."""
    rel_path = rel_path.lstrip("/")
    return str(_find_project_root() / rel_path)

class Settings(BaseSettings):
    # Database configuration
    DATABASE_URL: str = os.getenv(
        "POSTGRES_URL", 
        os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/gc_seg_db")
    )
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Cloudflare Turnstile (reemplazo de Google reCAPTCHA)
    TURNSTILE_SECRET_KEY: Optional[str] = os.getenv("TURNSTILE_SECRET_KEY", None)
    TURNSTILE_SITE_KEY: Optional[str] = os.getenv("TURNSTILE_SITE_KEY", None)
    
    # JWT & Autenticación de Administradores
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "giaconi-capra-pas-jwt-secret-key-prod-2026")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "480")) # 8 horas
    
    # CORS
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")

    @property
    def sqlalchemy_database_url(self) -> str:
        url = self.DATABASE_URL
        # Normalize postgres:// to postgresql:// for SQLAlchemy 2.0
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        # Anclar rutas SQLite relativas a la raíz del proyecto:
        # evita que "vercel dev" (CWD = .vercel/cache/...) o cualquier otro
        # directorio de trabajo escriban en un archivo .db distinto.
        if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
            url = f"sqlite:///{_resolve_sqlite_path(url[len('sqlite:///'):])}"
        return url

    @property
    def cors_origins(self) -> List[str]:
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
