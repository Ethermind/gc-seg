"""Tests for admin user management (roles and safeguards)."""


def _setup(client):
    """Creates the initial superadmin and returns (headers, user_id)."""
    r = client.post("/api/auth/setup", json={
        "username": "superadmin", "email": "super@test.dev",
        "password": "supersecret", "full_name": "Super",
    })
    assert r.status_code == 201
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, r.json()["user"]["id"]


def _create_user(client, headers, username, role="admin"):
    return client.post("/api/admin/users", json={
        "username": username, "email": f"{username}@test.dev",
        "password": "secret123", "role": role,
    }, headers=headers)


def _login_token(client, username, password):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


class TestAdminUsersCRUD:
    def test_create_admin(self, client):
        headers, _ = _setup(client)
        r = _create_user(client, headers, "editor1")
        assert r.status_code == 201
        assert r.json()["role"] == "admin"

    def test_duplicate_username_400(self, client):
        headers, _ = _setup(client)
        _create_user(client, headers, "editor1")
        r = _create_user(client, headers, "Editor1")  # normalizes to lowercase -> dup
        assert r.status_code == 400

    def test_list_users(self, client):
        headers, _ = _setup(client)
        _create_user(client, headers, "editor1")
        r = client.get("/api/admin/users", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_hashed_password_is_not_exposed(self, client):
        headers, _ = _setup(client)
        r = client.get("/api/admin/users", headers=headers)
        assert "hashed_password" not in r.text
        assert "secret" not in r.text


class TestAdminUsersSafeguards:
    def test_cannot_self_delete(self, client):
        headers, super_id = _setup(client)
        r = client.delete(f"/api/admin/users/{super_id}", headers=headers)
        assert r.status_code == 400
        assert "own administrator account" in r.json()["detail"]

    def test_admin_cannot_delete_superadmin(self, client):
        headers, super_id = _setup(client)
        _create_user(client, headers, "editor1")
        editor_headers = _login_token(client, "editor1", "secret123")
        r = client.delete(f"/api/admin/users/{super_id}", headers=editor_headers)
        assert r.status_code == 403

    def test_superadmin_can_delete_admin(self, client):
        headers, _ = _setup(client)
        uid = _create_user(client, headers, "editor1").json()["id"]
        r = client.delete(f"/api/admin/users/{uid}", headers=headers)
        assert r.status_code == 200
        assert len(client.get("/api/admin/users", headers=headers).json()) == 1

    def test_delete_nonexistent_404(self, client):
        headers, _ = _setup(client)
        assert client.delete("/api/admin/users/9999", headers=headers).status_code == 404


class TestChangePassword:
    def test_change_password_and_relogin(self, client):
        headers, _ = _setup(client)
        uid = _create_user(client, headers, "editor1").json()["id"]
        r = client.put(f"/api/admin/users/{uid}/password",
                       json={"new_password": "new-password-123"}, headers=headers)
        assert r.status_code == 200
        # the old one no longer works, the new one does
        assert client.post("/api/auth/login", json={"username": "editor1", "password": "secret123"}).status_code == 401
        assert client.post("/api/auth/login", json={"username": "editor1", "password": "new-password-123"}).status_code == 200

    def test_short_password_422(self, client):
        headers, _ = _setup(client)
        uid = _create_user(client, headers, "editor1").json()["id"]
        r = client.put(f"/api/admin/users/{uid}/password", json={"new_password": "x"}, headers=headers)
        assert r.status_code == 422

    def test_change_password_nonexistent_user_404(self, client):
        headers, _ = _setup(client)
        r = client.put("/api/admin/users/9999/password", json={"new_password": "long-enough"}, headers=headers)
        assert r.status_code == 404
