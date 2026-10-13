"""Tests for Reviews/Testimonials endpoints (public and admin)."""


def _review_payload(**over):
    data = {"name": "Juan Perez", "role": "Cliente", "rating": 5, "text": "Excellent service."}
    data.update(over)
    return data


class TestReviewPublicCreate:
    def test_post_remains_pending_moderation(self, client):
        # Even if the payload asks for is_approved=True, the public POST forces False.
        r = client.post("/api/reviews", json=_review_payload(is_approved=True))
        assert r.status_code == 201
        assert r.json()["is_approved"] is False

    def test_post_generates_avatar_initials(self, client):
        r = client.post("/api/reviews", json=_review_payload(name="sofia giannini"))
        assert r.json()["avatar"] == "SG"

    def test_turnstile_rejected_400(self, client, monkeypatch):
        async def _reject(token, ip=None):
            return False
        monkeypatch.setattr("api.routes.reviews.verify_turnstile", _reject)
        r = client.post("/api/reviews", json=_review_payload(turnstile_token="x"))
        assert r.status_code == 400

    def test_invalid_rating_422(self, client):
        assert client.post("/api/reviews", json=_review_payload(rating=9)).status_code == 422

    def test_public_listing_only_approved(self, client):
        client.post("/api/reviews", json=_review_payload(text="Pending approval"))
        assert client.get("/api/reviews").json() == []


class TestReviewAdminCRUD:
    def test_admin_creates_approved_directly(self, client, auth_headers):
        r = client.post("/api/admin/reviews", json=_review_payload(), headers=auth_headers)
        assert r.status_code == 201
        assert r.json()["is_approved"] is True

    def test_admin_approves_pending_review(self, client, auth_headers):
        rid = client.post("/api/reviews", json=_review_payload()).json()["id"]
        r = client.put(f"/api/admin/reviews/{rid}", json={"is_approved": True}, headers=auth_headers)
        assert r.status_code == 200
        assert any(rv["id"] == rid for rv in client.get("/api/reviews").json())

    def test_admin_editing_name_regenerates_avatar(self, client, auth_headers):
        rid = client.post("/api/admin/reviews", json=_review_payload(), headers=auth_headers).json()["id"]
        r = client.put(f"/api/admin/reviews/{rid}", json={"name": "Carlos Mendoza"}, headers=auth_headers)
        assert r.json()["avatar"] == "CM"

    def test_update_nonexistent_404(self, client, auth_headers):
        assert client.put("/api/admin/reviews/9999", json={"text": "x"}, headers=auth_headers).status_code == 404

    def test_delete(self, client, auth_headers):
        rid = client.post("/api/admin/reviews", json=_review_payload(), headers=auth_headers).json()["id"]
        assert client.delete(f"/api/admin/reviews/{rid}", headers=auth_headers).status_code == 200
        assert client.get("/api/reviews").json() == []

    def test_admin_filter_and_search(self, client, auth_headers):
        client.post("/api/admin/reviews", json=_review_payload(text="Great service", name="Ana Uno"), headers=auth_headers)
        client.post("/api/admin/reviews", json=_review_payload(text="Very good", name="Beto Dos"), headers=auth_headers)
        r = client.get("/api/admin/reviews?search=Beto", headers=auth_headers)
        assert len(r.json()) == 1 and r.json()[0]["name"] == "Beto Dos"
        r = client.get("/api/admin/reviews?approved=true", headers=auth_headers)
        assert len(r.json()) == 2
