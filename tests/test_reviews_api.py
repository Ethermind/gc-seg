"""Tests de endpoints de Reviews/Testimonios (públicos y admin)."""


def _review_payload(**over):
    data = {"name": "Juan Perez", "role": "Cliente", "rating": 5, "text": "Excelente atención."}
    data.update(over)
    return data


class TestReviewPublicCreate:
    def test_post_queda_pendiente_de_moderacion(self, client):
        # Aunque el payload pida is_approved=True, el POST público fuerza False.
        r = client.post("/api/reviews", json=_review_payload(is_approved=True))
        assert r.status_code == 201
        assert r.json()["is_approved"] is False

    def test_post_genera_avatar_initials(self, client):
        r = client.post("/api/reviews", json=_review_payload(name="sofia giannini"))
        assert r.json()["avatar"] == "SG"

    def test_turnstile_rechazado_400(self, client, monkeypatch):
        async def _reject(token, ip=None):
            return False
        monkeypatch.setattr("api.routes.reviews.verify_turnstile", _reject)
        r = client.post("/api/reviews", json=_review_payload(turnstile_token="x"))
        assert r.status_code == 400

    def test_rating_invalido_422(self, client):
        assert client.post("/api/reviews", json=_review_payload(rating=9)).status_code == 422

    def test_listado_publico_solo_aprobadas(self, client):
        client.post("/api/reviews", json=_review_payload(text="Pendiente de aprobación"))
        assert client.get("/api/reviews").json() == []


class TestReviewAdminCRUD:
    def test_admin_crea_aprobada_directamente(self, client, auth_headers):
        r = client.post("/api/admin/reviews", json=_review_payload(), headers=auth_headers)
        assert r.status_code == 201
        assert r.json()["is_approved"] is True

    def test_admin_aprueba_pendiente(self, client, auth_headers):
        rid = client.post("/api/reviews", json=_review_payload()).json()["id"]
        r = client.put(f"/api/admin/reviews/{rid}", json={"is_approved": True}, headers=auth_headers)
        assert r.status_code == 200
        assert any(rv["id"] == rid for rv in client.get("/api/reviews").json())

    def test_admin_editar_nombre_regenera_avatar(self, client, auth_headers):
        rid = client.post("/api/admin/reviews", json=_review_payload(), headers=auth_headers).json()["id"]
        r = client.put(f"/api/admin/reviews/{rid}", json={"name": "Carlos Mendoza"}, headers=auth_headers)
        assert r.json()["avatar"] == "CM"

    def test_editar_inexistente_404(self, client, auth_headers):
        assert client.put("/api/admin/reviews/9999", json={"text": "x"}, headers=auth_headers).status_code == 404

    def test_delete(self, client, auth_headers):
        rid = client.post("/api/admin/reviews", json=_review_payload(), headers=auth_headers).json()["id"]
        assert client.delete(f"/api/admin/reviews/{rid}", headers=auth_headers).status_code == 200
        assert client.get("/api/reviews").json() == []

    def test_filtro_y_busqueda_admin(self, client, auth_headers):
        client.post("/api/admin/reviews", json=_review_payload(text="Servicio genial", name="Ana Uno"), headers=auth_headers)
        client.post("/api/admin/reviews", json=_review_payload(text="Muy bueno", name="Beto Dos"), headers=auth_headers)
        r = client.get("/api/admin/reviews?search=Beto", headers=auth_headers)
        assert len(r.json()) == 1 and r.json()[0]["name"] == "Beto Dos"
        r = client.get("/api/admin/reviews?approved=true", headers=auth_headers)
        assert len(r.json()) == 2
