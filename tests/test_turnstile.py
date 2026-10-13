"""Tests de api.services.turnstile con red mockeada (sin salir a Cloudflare)."""
import asyncio

import api.services.turnstile as turnstile


def _verify(token="token", ip="1.2.3.4"):
    return asyncio.run(turnstile.verify_turnstile(token, ip))


class _FakeSettings:
    def __init__(self, secret=None, env="development"):
        self.TURNSTILE_SECRET_KEY = secret
        self.ENVIRONMENT = env


class _FakeAsyncClient:
    """Stub de httpx.AsyncClient para la llamada siteverify."""
    success = True

    def __init__(self, *a, **kw):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, *a, **kw):
        class _Resp:
            def json(self_inner):
                return {"success": _FakeAsyncClient.success}
        return _Resp()


class _BoomAsyncClient(_FakeAsyncClient):
    async def post(self, *a, **kw):
        raise ConnectionError("cloudflare caído (simulado)")


def test_bypass_en_development_sin_secret(monkeypatch):
    monkeypatch.setattr(turnstile, "settings", _FakeSettings(secret=None, env="development"))
    assert _verify() is True


def test_sin_secret_en_production_rechaza(monkeypatch):
    monkeypatch.setattr(turnstile, "settings", _FakeSettings(secret=None, env="production"))
    assert _verify() is False


def test_con_secret_sin_token_rechaza(monkeypatch):
    monkeypatch.setattr(turnstile, "settings", _FakeSettings(secret="s3cret", env="production"))
    assert _verify(token=None) is False


def test_verificacion_exitosa(monkeypatch):
    monkeypatch.setattr(turnstile, "settings", _FakeSettings(secret="s3cret", env="production"))
    monkeypatch.setattr(turnstile.httpx, "AsyncClient", _FakeAsyncClient)
    _FakeAsyncClient.success = True
    assert _verify() is True


def test_verificacion_rechazada_por_cloudflare(monkeypatch):
    monkeypatch.setattr(turnstile, "settings", _FakeSettings(secret="s3cret", env="production"))
    monkeypatch.setattr(turnstile.httpx, "AsyncClient", _FakeAsyncClient)
    _FakeAsyncClient.success = False
    assert _verify() is False


def test_falla_de_red_en_production_rechaza(monkeypatch):
    monkeypatch.setattr(turnstile, "settings", _FakeSettings(secret="s3cret", env="production"))
    monkeypatch.setattr(turnstile.httpx, "AsyncClient", _BoomAsyncClient)
    assert _verify() is False


def test_falla_de_red_en_development_hace_bypass(monkeypatch):
    monkeypatch.setattr(turnstile, "settings", _FakeSettings(secret="s3cret", env="development"))
    monkeypatch.setattr(turnstile.httpx, "AsyncClient", _BoomAsyncClient)
    assert _verify() is True
