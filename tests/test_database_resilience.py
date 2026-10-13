"""Tests for the degraded mode of api.database (lesson from the 2026-10-13 outage).

If the DB URL/driver is invalid, the engine becomes None and the app must:
- survive the import (never again FUNCTION_INVOCATION_FAILED),
- answer a clean JSON 503 on endpoints using get_db,
- answer 200 with status "degraded" on /api/health.
"""
import pytest
from fastapi import HTTPException

import api.database as db_mod
import api.routes.health as health_mod


class TestEngineNone:
    def test_get_db_returns_503_not_a_raw_exception(self, monkeypatch):
        monkeypatch.setattr(db_mod, "engine", None)
        gen = db_mod.get_db()
        with pytest.raises(HTTPException) as exc_info:
            next(gen)
        assert exc_info.value.status_code == 503
        assert "not available" in exc_info.value.detail

    def test_init_db_does_not_explode_with_engine_none(self, monkeypatch, caplog):
        monkeypatch.setattr(db_mod, "engine", None)
        import logging
        with caplog.at_level(logging.ERROR):
            db_mod.init_db()  # must not raise
        assert "init_db skipped" in caplog.text

    def test_health_responds_degraded_without_breaking(self, monkeypatch):
        monkeypatch.setattr(health_mod, "engine", None)
        result = health_mod.health_check()
        assert result["status"] == "degraded"
        assert result["db_driver"] is None
        assert "not initialized" in result["database"]


class TestPostgresOnlyGuard:
    def test_sqlite_urls_are_rejected(self):
        assert not db_mod._is_supported_url("sqlite:///local.db")

    def test_postgresql_urls_are_accepted(self):
        assert db_mod._is_supported_url("postgresql://u:p@localhost:5432/db")
        # config normalizes legacy/driver-suffixed schemes before this check
        assert db_mod._is_supported_url("postgresql://u:p@host/db?sslmode=require")


class TestHealthEndpoint:
    def test_health_healthy_with_live_db(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "healthy"
        assert body["database"] == "connected"
        # Deployed-build visibility surface:
        for key in ("python", "sqlalchemy", "db_driver", "environment", "timestamp"):
            assert key in body, f"missing {key} in /api/health"
        assert body["environment"] == "development"
        assert body["db_driver"] == "psycopg"  # in tests the DB is PostgreSQL too
