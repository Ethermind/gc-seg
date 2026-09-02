import os
from pydantic_settings import BaseSettings
from typing import List, Optional
from dotenv import load_dotenv

# Cargar .env.local (generado por Vercel CLI) y .env
load_dotenv(".env.local")
load_dotenv(".env")

class Settings(BaseSettings):
    # Database configuration
    DATABASE_URL: str = os.getenv(
        "POSTGRES_URL", 
        os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/gc_seg_db")
    )
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Google reCAPTCHA
    RECAPTCHA_SECRET_KEY: Optional[str] = os.getenv("RECAPTCHA_SECRET_KEY", None)
    RECAPTCHA_SITE_KEY: Optional[str] = os.getenv("RECAPTCHA_SITE_KEY", None)
    
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
