"""Tests de gestión de usuarios administradores (roles y salvaguardas)."""


def _setup(client):
    """Crea el superadmin inicial y devuelve (headers, user_id)."""
    r = client.post("/api/auth/setup", json={
        "username": "superadmin", "email": "super@test.dev",
        "password": "supersecret", "full_name": "Super",
    })
    assert r.status_code == 201
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, r.json()["user"]["id"]


def _crear_usuario(client, headers, username, role="admin"):
    return client.post("/api/admin/users", json={
        "username": username, "email": f"{username}@test.dev",
        "password": "secret123", "role": role,
    }, headers=headers)


def _login_token(client, username, password):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


class TestAdminUsersCRUD:
    def test_crear_admin(self, client):
        headers, _ = _setup(client)
        r = _crear_usuario(client, headers, "editor1")
        assert r.status_code == 201
        assert r.json()["role"] == "admin"

    def test_duplicado_por_username_400(self, client):
        headers, _ = _setup(client)
        _crear_usuario(client, headers, "editor1")
        r = _crear_usuario(client, headers, "Editor1")  # normaliza a minúsculas -> dup
        assert r.status_code == 400

    def test_lista_usuarios(self, client):
        headers, _ = _setup(client)
        _crear_usuario(client, headers, "editor1")
        r = client.get("/api/admin/users", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_password_hasheada_no_expuesta(self, client):
        headers, _ = _setup(client)
        r = client.get("/api/admin/users", headers=headers)
        assert "hashed_password" not in r.text
        assert "secret" not in r.text


class TestAdminUsersSalvaguardas:
    def test_no_puede_autoeliminar(self, client):
        headers, super_id = _setup(client)
        r = client.delete(f"/api/admin/users/{super_id}", headers=headers)
        assert r.status_code == 400
        assert "propia" in r.json()["detail"]

    def test_admin_no_puede_eliminar_superadmin(self, client):
        headers, super_id = _setup(client)
        _crear_usuario(client, headers, "editor1")
        editor_headers = _login_token(client, "editor1", "secret123")
        r = client.delete(f"/api/admin/users/{super_id}", headers=editor_headers)
        assert r.status_code == 403

    def test_superadmin_si_elimina_admin(self, client):
        headers, _ = _setup(client)
        uid = _crear_usuario(client, headers, "editor1").json()["id"]
        r = client.delete(f"/api/admin/users/{uid}", headers=headers)
        assert r.status_code == 200
        assert client.get("/api/admin/users", headers=headers).json().__len__() == 1

    def test_eliminar_inexistente_404(self, client):
        headers, _ = _setup(client)
        assert client.delete("/api/admin/users/9999", headers=headers).status_code == 404


class TestChangePassword:
    def test_cambiar_password_y_reloguear(self, client):
        headers, _ = _setup(client)
        uid = _crear_usuario(client, headers, "editor1").json()["id"]
        r = client.put(f"/api/admin/users/{uid}/password",
                       json={"new_password": "nueva-clave-123"}, headers=headers)
        assert r.status_code == 200
        # la vieja ya no sirve, la nueva sí
        assert client.post("/api/auth/login", json={"username": "editor1", "password": "secret123"}).status_code == 401
        assert client.post("/api/auth/login", json={"username": "editor1", "password": "nueva-clave-123"}).status_code == 200

    def test_password_corta_422(self, client):
        headers, _ = _setup(client)
        uid = _crear_usuario(client, headers, "editor1").json()["id"]
        r = client.put(f"/api/admin/users/{uid}/password", json={"new_password": "x"}, headers=headers)
        assert r.status_code == 422

    def test_cambiar_password_usuario_inexistente_404(self, client):
        headers, _ = _setup(client)
        r = client.put("/api/admin/users/9999/password", json={"new_password": "larga-suficiente"}, headers=headers)
        assert r.status_code == 404
