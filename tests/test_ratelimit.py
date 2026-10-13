"""Tests for slowapi rate limiting (10 req/min on contact and reviews).

The rest of the suite runs with the limiter disabled (autouse fixture);
here it is explicitly re-enabled and the in-memory storage is reset.
"""
import pytest

from api.ratelimit import limiter


def _reset_limiter():
    """slowapi 0.1.x: Limiter.reset() if available; otherwise internals."""
    if hasattr(limiter, "reset"):
        limiter.reset()
    else:  # pragma: no cover - defensive fallback
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
    def test_eleven_attempts_and_the_twelfth_is_429(self, client, limiter_on):
        # turnstile is bypassed (development + no secret) -> does not interfere
        for i in range(10):
            r = client.post("/api/contact", json=_contact_payload())
            assert r.status_code == 201, f"attempt {i + 1} should pass: {r.status_code}"
        r = client.post("/api/contact", json=_contact_payload())
        assert r.status_code == 429

    def test_429_returns_understandable_json(self, client, limiter_on):
        for _ in range(11):
            r = client.post("/api/contact", json=_contact_payload())
        assert r.status_code == 429
        assert "error" in r.json() or "detail" in r.json()
