"""
Fixtures compartidos de la suite de tests.

IMPORTANTE: las variables de entorno se fijan ANTES de importar cualquier
módulo de la app, porque `api.database` crea el engine al importarse.
Se usa una base SQLite temporal por corrida: hermética y rápida.
"""
import os
import sys
import tempfile

_TMPDIR = tempfile.mkdtemp(prefix="gc-pytest-")
_SQLITE_URL = f"sqlite:///{_TMPDIR}/test.db"
# POSTGRES_URL tiene precedencia sobre DATABASE_URL en api/config.py; ambas se
# fijan a la misma SQLite temporal para que ni el entorno local ni los archivos
# .env/.env.local (load_dotenv NO pisa vars ya presentes) desvíen los tests
# hacia una base real.
os.environ["POSTGRES_URL"] = _SQLITE_URL
os.environ["DATABASE_URL"] = _SQLITE_URL
os.environ["ENVIRONMENT"] = "development"        # Turnstile bypass sin secret
os.environ["TURNSTILE_SECRET_KEY"] = ""          # determinismo aunque .env defina claves

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient

from api.index import app
from api.database import SessionLocal
from api import models
from api.ratelimit import limiter


@pytest.fixture(scope="session")
def client():
    """TestClient compartido; la app crea las tablas en la SQLite temporal al importar."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    """Borra todas las filas entre tests (DB limpia por caso)."""
    db = SessionLocal()
    try:
        for model in (models.FAQ, models.Coverage, models.Manual,
                      models.Review, models.ContactLead, models.AdminUser):
            db.query(model).delete()
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture(autouse=True)
def _rate_limit_off():
    """Rate limiting deshabilitado por defecto para no interferir entre tests.
    El test específico de rate limit lo re-habilita explícitamente."""
    limiter.enabled = False
    yield
    limiter.enabled = True


@pytest.fixture
def auth_headers(client, clean_db):
    """Crea un superadmin vía /setup (DB limpia) y devuelve headers con Bearer token."""
    res = client.post("/api/auth/setup", json={
        "username": "superadmin",
        "email": "super@test.dev",
        "password": "supersecret",
        "full_name": "Super Test",
    })
    assert res.status_code == 201, res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
