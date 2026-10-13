"""Tests del endpoint público de contacto/cotización (/api/contact)."""


def _lead_payload(**over):
    data = {
        "nombre": "Juan Perez",
        "telefono": "+54 9 341 555-1234",
        "email": "juan@test.com",
        "producto": "Auto",
        "mensaje": "Quiero cotizar",
        "wsp": True,
        "aceptarDatos": True,
    }
    data.update(over)
    return data


class TestContactCreate:
    def test_lead_se_crea_con_status_nuevo_ip_y_user_agent(self, client):
        r = client.post("/api/contact", json=_lead_payload(), headers={"user-agent": "pytest-agent"})
        assert r.status_code == 201
        body = r.json()
        assert body["success"] is True and body["id"] > 0

    def test_email_invalido_422(self, client):
        assert client.post("/api/contact", json=_lead_payload(email="mal")).status_code == 422

    def test_sin_consentimiento_422(self, client):
        assert client.post("/api/contact", json=_lead_payload(aceptarDatos=False)).status_code == 422

    def test_sin_nombre_422(self, client):
        assert client.post("/api/contact", json=_lead_payload(nombre="")).status_code == 422

    def test_turnstile_rechazado_400(self, client, monkeypatch):
        async def _reject(token, ip=None):
            return False
        monkeypatch.setattr("api.routes.contact.verify_turnstile", _reject)
        r = client.post("/api/contact", json=_lead_payload(turnstile_token="x"))
        assert r.status_code == 400

    def test_mensaje_es_opcional(self, client):
        payload = _lead_payload()
        del payload["mensaje"]
        assert client.post("/api/contact", json=payload).status_code == 201
