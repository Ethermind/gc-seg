"""Tests de la gestión de leads desde el panel admin."""


def _crear_lead(client, nombre="Juan Perez", email="juan@test.com"):
    r = client.post("/api/contact", json={
        "nombre": nombre, "telefono": "3415551234", "email": email,
        "producto": "Auto", "mensaje": "Consulta", "aceptarDatos": True,
    })
    assert r.status_code == 201
    return r.json()["id"]


class TestLeadsAdmin:
    def test_lista_requiere_token(self, client):
        assert client.get("/api/admin/leads").status_code in (401, 403)

    def test_listar_leads(self, client, auth_headers):
        _crear_lead(client)
        r = client.get("/api/admin/leads", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["status"] == "nuevo"

    def test_buscar_por_nombre(self, client, auth_headers):
        _crear_lead(client, nombre="Carlos Uno", email="c1@t.com")
        _crear_lead(client, nombre="Beto Dos", email="b2@t.com")
        r = client.get("/api/admin/leads?search=Beto", headers=auth_headers)
        assert len(r.json()) == 1 and r.json()[0]["nombre"] == "Beto Dos"

    def test_filtro_por_status(self, client, auth_headers):
        lid = _crear_lead(client)
        client.patch(f"/api/admin/leads/{lid}", json={"status": "cerrado"}, headers=auth_headers)
        r = client.get("/api/admin/leads?status=cerrado", headers=auth_headers)
        assert len(r.json()) == 1
        r = client.get("/api/admin/leads?status=nuevo", headers=auth_headers)
        assert len(r.json()) == 0

    def test_patch_status_valido(self, client, auth_headers):
        lid = _crear_lead(client)
        r = client.patch(f"/api/admin/leads/{lid}", json={"status": "en_gestion"}, headers=auth_headers)
        assert r.status_code == 200 and r.json()["status"] == "en_gestion"

    def test_patch_status_invalido_422(self, client, auth_headers):
        lid = _crear_lead(client)
        r = client.patch(f"/api/admin/leads/{lid}", json={"status": "descartado"}, headers=auth_headers)
        assert r.status_code == 422

    def test_patch_inexistente_404(self, client, auth_headers):
        assert client.patch("/api/admin/leads/9999", json={"status": "cerrado"}, headers=auth_headers).status_code == 404

    def test_crear_lead_manual_desde_admin(self, client, auth_headers):
        r = client.post("/api/admin/leads", json={
            "nombre": "Manual Lead", "telefono": "3415550000",
            "email": None, "producto": "Hogar", "mensaje": "Cargado desde el panel",
        }, headers=auth_headers)
        assert r.status_code == 201
        assert r.json()["status"] == "nuevo"

    def test_delete_lead(self, client, auth_headers):
        lid = _crear_lead(client)
        assert client.delete(f"/api/admin/leads/{lid}", headers=auth_headers).status_code == 200
        assert client.get("/api/admin/leads", headers=auth_headers).json() == []
