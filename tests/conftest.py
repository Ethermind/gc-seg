"""
Fixtures compartidos de la suite de tests.

IMPORTANTE: las variables de entorno se fijan ANTES de importar cualquier
módulo de la app, porque `api.database` crea el engine al importarse.
La suite corre contra una base PostgreSQL dedicada (gc_seg_test por defecto;
sobreescribible con TEST_DATABASE_URL, p.ej. en CI): paridad total con
producción. La base se crea automáticamente si no existe.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.pg_testutils import ensure_database

_TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/gc_seg_test"
)
# POSTGRES_URL tiene precedencia sobre DATABASE_URL en api/config.py; ambas se
# fijan a la misma base de test para que ni el entorno local ni los archivos
# .env/.env.local (load_dotenv NO pisa vars ya presentes) desvíen los tests
# hacia una base real.
os.environ["POSTGRES_URL"] = _TEST_DB_URL
os.environ["DATABASE_URL"] = _TEST_DB_URL
os.environ["ENVIRONMENT"] = "development"        # Turnstile bypass sin secret
os.environ["TURNSTILE_SECRET_KEY"] = ""          # determinismo aunque .env defina claves

# Idempotente: crea gc_seg_test si falta (primer uso local o job de CI).
ensure_database(_TEST_DB_URL)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from api.index import app
from api.database import SessionLocal
from api.ratelimit import limiter

# Tablas administradas por la suite, en cualquier orden (CASCADE resuelve FKs).
_TABLES = "faqs, coverages, manuals, reviews, contact_leads, admin_users"


@pytest.fixture(scope="session")
def client():
    """TestClient compartido; la app crea las tablas en la base de test al importar."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    """Borra todas las filas entre tests y reinicia las secuencias de ids
    (RESTART IDENTITY): cada caso arranca con base limpia e ids previsibles."""
    db = SessionLocal()
    try:
        db.execute(text(f"TRUNCATE TABLE {_TABLES} RESTART IDENTITY CASCADE"))
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
