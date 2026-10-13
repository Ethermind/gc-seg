"""Tests del rate limiting con slowapi (10 req/min en contact y reviews).

El resto de la suite corre con el limiter deshabilitado (fixture autouse);
acá se habilita explícitamente y se resetea el storage in-memory.
"""
import pytest

from api.ratelimit import limiter


def _reset_limiter():
    """slowapi 0.1.x: Limiter.reset() si existe; si no, storage interno."""
    if hasattr(limiter, "reset"):
        limiter.reset()
    else:  # pragma: no cover - fallback defensivo
        limiter._storage.reset()


@pytest.fixture
def limiter_on():
    limiter.enabled = True
    _reset_limiter()
    yield
    limiter.enabled = False
    _reset_limiter()


def _contact_payload():
    return {
        "nombre": "Rate Tester", "telefono": "3415551234",
        "mensaje": "spam check", "aceptarDatos": True,
    }


class TestRateLimitContact:
    def test_once_pegadas_y_la_doce_es_429(self, client, limiter_on):
        # turnstile en bypass (development + sin secret) -> no interfiere
        for i in range(10):
            r = client.post("/api/contact", json=_contact_payload())
            assert r.status_code == 201, f"pegada {i + 1} debería pasar: {r.status_code}"
        r = client.post("/api/contact", json=_contact_payload())
        assert r.status_code == 429

    def test_429_devuelve_json_entendible(self, client, limiter_on):
        for _ in range(11):
            r = client.post("/api/contact", json=_contact_payload())
        assert r.status_code == 429
        assert "error" in r.json() or "detail" in r.json()
