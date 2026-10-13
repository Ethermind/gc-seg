"""Tests for api.services.turnstile with the network mocked (no Cloudflare calls)."""
import asyncio

import api.services.turnstile as turnstile


def _verify(token="token", ip="1.2.3.4"):
    return asyncio.run(turnstile.verify_turnstile(token, ip))


class _FakeSettings:
    def __init__(self, secret=None, env="development"):
        self.TURNSTILE_SECRET_KEY = secret
        self.ENVIRONMENT = env


class _FakeAsyncClient:
    """Stub for httpx.AsyncClient for the siteverify call."""
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
        raise ConnectionError("cloudflare down (simulated)")


def test_bypass_in_development_without_secret(monkeypatch):
    monkeypatch.setattr(turnstile, "settings", _FakeSettings(secret=None, env="development"))
    assert _verify() is True


def test_no_secret_in_production_rejects(monkeypatch):
    monkeypatch.setattr(turnstile, "settings", _FakeSettings(secret=None, env="production"))
    assert _verify() is False


def test_with_secret_but_no_token_rejects(monkeypatch):
    monkeypatch.setattr(turnstile, "settings", _FakeSettings(secret="s3cret", env="production"))
    assert _verify(token=None) is False


def test_successful_verification(monkeypatch):
    monkeypatch.setattr(turnstile, "settings", _FakeSettings(secret="s3cret", env="production"))
    monkeypatch.setattr(turnstile.httpx, "AsyncClient", _FakeAsyncClient)
    _FakeAsyncClient.success = True
    assert _verify() is True


def test_verification_rejected_by_cloudflare(monkeypatch):
    monkeypatch.setattr(turnstile, "settings", _FakeSettings(secret="s3cret", env="production"))
    monkeypatch.setattr(turnstile.httpx, "AsyncClient", _FakeAsyncClient)
    _FakeAsyncClient.success = False
    assert _verify() is False


def test_network_failure_in_production_rejects(monkeypatch):
    monkeypatch.setattr(turnstile, "settings", _FakeSettings(secret="s3cret", env="production"))
    monkeypatch.setattr(turnstile.httpx, "AsyncClient", _BoomAsyncClient)
    assert _verify() is False


def test_network_failure_in_development_bypasses(monkeypatch):
    monkeypatch.setattr(turnstile, "settings", _FakeSettings(secret="s3cret", env="development"))
    monkeypatch.setattr(turnstile.httpx, "AsyncClient", _BoomAsyncClient)
    assert _verify() is True
