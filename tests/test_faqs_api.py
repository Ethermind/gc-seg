"""Tests de endpoints de FAQs (públicos y admin)."""


def _faq_payload(**over):
    data = {
        "pregunta": "¿Pregunta de prueba?",
        "respuesta": "Respuesta de prueba.",
        "categoria": "general",
        "orden": 1,
        "activo": True,
    }
    data.update(over)
    return data


class TestFaqAdminCRUD:
    def test_crear_faq_201(self, client, auth_headers):
        r = client.post("/api/faqs/admin", json=_faq_payload(), headers=auth_headers)
        assert r.status_code == 201
        assert r.json()["id"] > 0

    def test_crear_sin_token_401_o_403(self, client):
        r = client.post("/api/faqs/admin", json=_faq_payload())
        assert r.status_code in (401, 403)

    def test_dos_faqs_consecutivas_tienen_ids_crecientes(self, client, auth_headers):
        # Regresión: secuencias desincronizadas en PG rompían el 1er insert.
        r1 = client.post("/api/faqs/admin", json=_faq_payload(pregunta="¿Una?"), headers=auth_headers)
        r2 = client.post("/api/faqs/admin", json=_faq_payload(pregunta="¿Dos?"), headers=auth_headers)
        assert r1.status_code == 201 and r2.status_code == 201
        assert r2.json()["id"] > r1.json()["id"]

    def test_actualizar_faq(self, client, auth_headers):
        fid = client.post("/api/faqs/admin", json=_faq_payload(), headers=auth_headers).json()["id"]
        r = client.put(f"/api/faqs/admin/{fid}", json={"respuesta": "Editada"}, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["respuesta"] == "Editada"
        assert r.json()["pregunta"] == "¿Pregunta de prueba?"  # no cambió

    def test_actualizar_inexistente_404(self, client, auth_headers):
        assert client.put("/api/faqs/admin/9999", json={"activo": False}, headers=auth_headers).status_code == 404

    def test_eliminar_faq(self, client, auth_headers):
        fid = client.post("/api/faqs/admin", json=_faq_payload(), headers=auth_headers).json()["id"]
        assert client.delete(f"/api/faqs/admin/{fid}", headers=auth_headers).status_code == 200
        assert client.get("/api/faqs", headers=auth_headers)  # sanity
        r = client.get(f"/api/faqs/admin", headers=auth_headers)
        assert all(f["id"] != fid for f in r.json())

    def test_eliminar_inexistente_404(self, client, auth_headers):
        assert client.delete("/api/faqs/admin/9999", headers=auth_headers).status_code == 404


class TestFaqPublic:
    def test_publico_solo_lista_activas(self, client, auth_headers):
        client.post("/api/faqs/admin", json=_faq_payload(pregunta="¿Activa?", activo=True), headers=auth_headers)
        client.post("/api/faqs/admin", json=_faq_payload(pregunta="¿Inactiva?", activo=False), headers=auth_headers)
        r = client.get("/api/faqs")
        assert r.status_code == 200
        preguntas = [f["pregunta"] for f in r.json()]
        assert "¿Activa?" in preguntas
        assert "¿Inactiva?" not in preguntas

    def test_publico_solo_activos_false_las_muestra_todas(self, client, auth_headers):
        client.post("/api/faqs/admin", json=_faq_payload(activo=False), headers=auth_headers)
        r = client.get("/api/faqs?solo_activos=false")
        assert len(r.json()) == 1

    def test_publico_ordena_por_orden(self, client, auth_headers):
        client.post("/api/faqs/admin", json=_faq_payload(pregunta="¿Segunda?", orden=2), headers=auth_headers)
        client.post("/api/faqs/admin", json=_faq_payload(pregunta="¿Primera?", orden=1), headers=auth_headers)
        r = client.get("/api/faqs")
        assert r.json()[0]["pregunta"] == "¿Primera?"

    def test_filtro_por_categoria(self, client, auth_headers):
        client.post("/api/faqs/admin", json=_faq_payload(pregunta="¿Gral?", categoria="general"), headers=auth_headers)
        client.post("/api/faqs/admin", json=_faq_payload(pregunta="¿Coti?", categoria="cotizacion"), headers=auth_headers)
        r = client.get("/api/faqs?categoria=cotizacion")
        assert [f["pregunta"] for f in r.json()] == ["¿Coti?"]
