"""Tests del modo degradado de api.database (aprendizaje del outage 13/10/2026).

Si la URL/driver de la DB es inválido, el engine queda en None y la app debe:
- sobrevivir el import (nunca más FUNCTION_INVOCATION_FAILED),
- responder 503 JSON limpio en endpoints que usan get_db,
- responder 200 con status "degraded" en /api/health.
"""
import pytest
from fastapi import HTTPException

import api.database as db_mod
import api.routes.health as health_mod


class TestEngineNone:
    def test_get_db_devuelve_503_no_excepcion_cruda(self, monkeypatch):
        monkeypatch.setattr(db_mod, "engine", None)
        gen = db_mod.get_db()
        with pytest.raises(HTTPException) as exc_info:
            next(gen)
        assert exc_info.value.status_code == 503
        assert "base de datos no está disponible" in exc_info.value.detail

    def test_init_db_no_explota_con_engine_none(self, monkeypatch, caplog):
        monkeypatch.setattr(db_mod, "engine", None)
        import logging
        with caplog.at_level(logging.ERROR):
            db_mod.init_db()  # no debe levantar excepción
        assert "init_db omitido" in caplog.text

    def test_health_responde_degraded_sin_romperse(self, monkeypatch):
        monkeypatch.setattr(health_mod, "engine", None)
        result = health_mod.health_check()
        assert result["status"] == "degraded"
        assert result["db_driver"] is None
        assert "no inicializado" in result["database"]


class TestHealthEndpoint:
    def test_health_healthy_con_db_viva(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "healthy"
        assert body["database"] == "connected"
        # Superficie de visibilidad del build desplegado:
        for clave in ("python", "sqlalchemy", "db_driver", "environment", "timestamp"):
            assert clave in body, f"falta {clave} en /api/health"
        assert body["environment"] == "development"
        assert body["db_driver"] == "pysqlite"  # en tests la DB es sqlite temporal
