"""Tests de endpoints de Coberturas (públicos y admin)."""


def _cov_payload(**over):
    data = {
        "categoria": "personas",
        "titulo": "Auto",
        "icono": "car",
        "descripcion": "Descripción de prueba.",
        "orden": 1,
        "activo": True,
    }
    data.update(over)
    return data


class TestCoverageAdminCRUD:
    def test_crear_cobertura_201(self, client, auth_headers):
        r = client.post("/api/coverages/admin", json=_cov_payload(), headers=auth_headers)
        assert r.status_code == 201
        assert r.json()["id"] > 0

    def test_categoria_invalida_422(self, client, auth_headers):
        r = client.post("/api/coverages/admin", json=_cov_payload(categoria="mascotas"), headers=auth_headers)
        assert r.status_code == 422

    def test_crear_sin_token_rechaza(self, client):
        assert client.post("/api/coverages/admin", json=_cov_payload()).status_code in (401, 403)

    def test_actualizar_y_toggle(self, client, auth_headers):
        cid = client.post("/api/coverages/admin", json=_cov_payload(), headers=auth_headers).json()["id"]
        r = client.put(f"/api/coverages/admin/{cid}", json={"activo": False, "badge": "Nuevo"}, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["activo"] is False and r.json()["badge"] == "Nuevo"

    def test_actualizar_404(self, client, auth_headers):
        assert client.put("/api/coverages/admin/9999", json={"activo": False}, headers=auth_headers).status_code == 404

    def test_eliminar(self, client, auth_headers):
        cid = client.post("/api/coverages/admin", json=_cov_payload(), headers=auth_headers).json()["id"]
        assert client.delete(f"/api/coverages/admin/{cid}", headers=auth_headers).status_code == 200
        assert client.delete(f"/api/coverages/admin/{cid}", headers=auth_headers).status_code == 404


class TestCoveragePublic:
    def test_publico_solo_activas_por_categoria(self, client, auth_headers):
        client.post("/api/coverages/admin", json=_cov_payload(titulo="Auto"), headers=auth_headers)
        client.post("/api/coverages/admin", json=_cov_payload(categoria="empresas", titulo="ART", icono="hard-hat"), headers=auth_headers)
        client.post("/api/coverages/admin", json=_cov_payload(titulo="Moto", activo=False), headers=auth_headers)
        r = client.get("/api/coverages?categoria=personas")
        assert r.status_code == 200
        titulos = [c["titulo"] for c in r.json()]
        assert titulos == ["Auto"]

    def test_publico_solo_activos_false(self, client, auth_headers):
        client.post("/api/coverages/admin", json=_cov_payload(activo=False), headers=auth_headers)
        assert len(client.get("/api/coverages").json()) == 0
        assert len(client.get("/api/coverages?solo_activos=false").json()) == 1
