"""Tests de endpoints de autenticación: setup inicial, login, perfil."""


def _setup(client, username="admin", password="1234567890", email="admin@test.dev"):
    return client.post("/api/auth/setup", json={
        "username": username, "email": email, "password": password, "full_name": "Admin Test",
    })


class TestSetup:
    def test_setup_crea_superadmin_y_devuelve_token(self, client):
        r = _setup(client)
        assert r.status_code == 201
        body = r.json()
        assert body["access_token"]
        assert body["user"]["role"] == "superadmin"
        assert body["user"]["is_active"] is True

    def test_segundo_setup_rechazado(self, client):
        _setup(client)
        r = _setup(client, username="otro", email="otro@test.dev")
        assert r.status_code == 400

    def test_setup_status_refleja_si_hay_admins(self, client):
        assert client.get("/api/auth/setup-status").json()["needs_setup"] is True
        _setup(client)
        assert client.get("/api/auth/setup-status").json()["needs_setup"] is False


class TestLogin:
    def test_login_ok_devuelve_token_y_actualiza_last_login(self, client):
        _setup(client)
        r = client.post("/api/auth/login", json={"username": "admin", "password": "1234567890"})
        assert r.status_code == 200
        assert r.json()["access_token"]
        assert r.json()["user"]["last_login"] is not None

    def test_login_acepta_email_como_identificador(self, client):
        _setup(client)
        r = client.post("/api/auth/login", json={"username": "ADMIN@test.dev", "password": "1234567890"})
        assert r.status_code == 200

    def test_password_incorrecta_401(self, client):
        _setup(client)
        r = client.post("/api/auth/login", json={"username": "admin", "password": "incorrecta"})
        assert r.status_code == 401

    def test_usuario_inexistente_401(self, client):
        r = client.post("/api/auth/login", json={"username": "nadie", "password": "x"})
        assert r.status_code == 401


class TestMe:
    def test_me_con_token(self, client):
        token = _setup(client).json()["access_token"]
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["username"] == "admin"

    def test_me_sin_token_401(self, client):
        assert client.get("/api/auth/me").status_code == 401

    def test_me_con_token_inventado_401(self, client):
        r = client.get("/api/auth/me", headers={"Authorization": "Bearer inventado"})
        assert r.status_code == 401
