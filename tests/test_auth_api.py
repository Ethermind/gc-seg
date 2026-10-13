"""Tests for authentication endpoints: initial setup, login, profile."""


def _setup(client, username="admin", password="1234567890", email="admin@test.dev"):
    return client.post("/api/auth/setup", json={
        "username": username, "email": email, "password": password, "full_name": "Admin Test",
    })


class TestSetup:
    def test_setup_creates_superadmin_and_returns_token(self, client):
        r = _setup(client)
        assert r.status_code == 201
        body = r.json()
        assert body["access_token"]
        assert body["user"]["role"] == "superadmin"
        assert body["user"]["is_active"] is True

    def test_second_setup_is_rejected(self, client):
        _setup(client)
        r = _setup(client, username="other", email="other@test.dev")
        assert r.status_code == 400

    def test_setup_status_reflects_whether_admins_exist(self, client):
        assert client.get("/api/auth/setup-status").json()["needs_setup"] is True
        _setup(client)
        assert client.get("/api/auth/setup-status").json()["needs_setup"] is False


class TestLogin:
    def test_login_ok_returns_token_and_updates_last_login(self, client):
        _setup(client)
        r = client.post("/api/auth/login", json={"username": "admin", "password": "1234567890"})
        assert r.status_code == 200
        assert r.json()["access_token"]
        assert r.json()["user"]["last_login"] is not None

    def test_login_accepts_email_as_identifier(self, client):
        _setup(client)
        r = client.post("/api/auth/login", json={"username": "ADMIN@test.dev", "password": "1234567890"})
        assert r.status_code == 200

    def test_wrong_password_401(self, client):
        _setup(client)
        r = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
        assert r.status_code == 401

    def test_nonexistent_user_401(self, client):
        r = client.post("/api/auth/login", json={"username": "nobody", "password": "x"})
        assert r.status_code == 401


class TestMe:
    def test_me_with_token(self, client):
        token = _setup(client).json()["access_token"]
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["username"] == "admin"

    def test_me_without_token_401(self, client):
        assert client.get("/api/auth/me").status_code == 401

    def test_me_with_made_up_token_401(self, client):
        r = client.get("/api/auth/me", headers={"Authorization": "Bearer madeup"})
        assert r.status_code == 401
