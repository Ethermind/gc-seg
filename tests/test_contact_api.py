"""Tests for the public contact/quote endpoint (/api/contact)."""


def _lead_payload(**over):
    data = {
        "nombre": "Juan Perez",
        "telefono": "+54 9 341 555-1234",
        "email": "juan@test.com",
        "producto": "Auto",
        "mensaje": "I want a quote",
        "wsp": True,
        "aceptarDatos": True,
    }
    data.update(over)
    return data


class TestContactCreate:
    def test_lead_is_created_with_status_nuevo_success_and_id(self, client):
        r = client.post("/api/contact", json=_lead_payload(), headers={"user-agent": "pytest-agent"})
        assert r.status_code == 201
        body = r.json()
        assert body["success"] is True and body["id"] > 0

    def test_invalid_email_422(self, client):
        assert client.post("/api/contact", json=_lead_payload(email="bad")).status_code == 422

    def test_without_consent_422(self, client):
        assert client.post("/api/contact", json=_lead_payload(aceptarDatos=False)).status_code == 422

    def test_without_name_422(self, client):
        assert client.post("/api/contact", json=_lead_payload(nombre="")).status_code == 422

    def test_turnstile_rejected_400(self, client, monkeypatch):
        async def _reject(token, ip=None):
            return False
        monkeypatch.setattr("api.routes.contact.verify_turnstile", _reject)
        r = client.post("/api/contact", json=_lead_payload(turnstile_token="x"))
        assert r.status_code == 400

    def test_mensaje_is_optional(self, client):
        payload = _lead_payload()
        del payload["mensaje"]
        assert client.post("/api/contact", json=payload).status_code == 201
