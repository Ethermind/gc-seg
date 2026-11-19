"""Tests for the Companies ("Compañías en las que confiamos") endpoints:
public list + logo download; admin CRUD with optional logo upload/remove."""

PNG_LOGO = b"\x89PNG\r\n\x1a\n" + b"fake-png-data"
JPG_LOGO = b"\xff\xd8\xff\xe0" + b"fake-jpeg-data"


def _create(client, headers, nombre="Federación Patronal", url=None, orden=1,
            activo=True, logo_bytes=None, logo_filename="logo.png", logo_type="image/png"):
    data = {"nombre": nombre, "orden": str(orden), "activo": "true" if activo else "false"}
    if url is not None:
        data["url"] = url
    files = None
    if logo_bytes is not None:
        files = {"logo": (logo_filename, logo_bytes, logo_type)}
    return client.post("/api/companies/admin", data=data, files=files, headers=headers)


class TestPublicListing:
    def test_requires_no_auth_and_orders_by_orden(self, client, auth_headers):
        _create(client, auth_headers, nombre="B", orden=2)
        _create(client, auth_headers, nombre="A", orden=1)
        res = client.get("/api/companies")
        assert res.status_code == 200
        assert [c["nombre"] for c in res.json()] == ["A", "B"]

    def test_hides_inactive_and_has_logo_flag(self, client, auth_headers):
        _create(client, auth_headers, nombre="Con logo", logo_bytes=PNG_LOGO)
        _create(client, auth_headers, nombre="Sin logo")
        _create(client, auth_headers, nombre="Inactiva", activo=False)
        res = client.get("/api/companies")
        names = [c["nombre"] for c in res.json()]
        assert names == ["Con logo", "Sin logo"]
        assert res.json()[0]["has_logo"] is True
        assert res.json()[0]["logo_content_type"] == "image/png"
        assert res.json()[1]["has_logo"] is False

    def test_empty_list(self, client):
        assert client.get("/api/companies").json() == []


class TestLogoDownload:
    def test_download_identical_bytes_and_content_type(self, client, auth_headers):
        cid = _create(client, auth_headers, logo_bytes=PNG_LOGO).json()["id"]
        res = client.get(f"/api/companies/{cid}/logo")
        assert res.status_code == 200
        assert res.content == PNG_LOGO
        assert res.headers["content-type"] == "image/png"
        assert "inline" in res.headers["content-disposition"]

    def test_download_without_logo_404(self, client, auth_headers):
        cid = _create(client, auth_headers, nombre="Sin logo").json()["id"]
        assert client.get(f"/api/companies/{cid}/logo").status_code == 404

    def test_download_nonexistent_404(self, client):
        assert client.get("/api/companies/9999/logo").status_code == 404


class TestAdminCrud:
    def test_admin_endpoints_require_auth(self, client):
        assert client.get("/api/companies/admin").status_code in (401, 403)
        assert client.post("/api/companies/admin", data={"nombre": "X"}).status_code in (401, 403)
        assert client.put("/api/companies/admin/1", json={"nombre": "X"}).status_code in (401, 403)
        assert client.delete("/api/companies/admin/1").status_code in (401, 403)

    def test_admin_list_includes_inactive(self, client, auth_headers):
        _create(client, auth_headers, nombre="Activa")
        _create(client, auth_headers, nombre="Inactiva", activo=False)
        res = client.get("/api/companies/admin", headers=auth_headers)
        assert [c["nombre"] for c in res.json()] == ["Activa", "Inactiva"]

    def test_create_without_logo_201(self, client, auth_headers):
        res = _create(client, auth_headers, nombre="Mercantil Andina", url="https://www.mercantilandina.com.ar", orden=2)
        assert res.status_code == 201, res.text
        body = res.json()
        assert body["nombre"] == "Mercantil Andina"
        assert body["url"] == "https://www.mercantilandina.com.ar"
        assert body["has_logo"] is False
        assert body["activo"] is True

    def test_create_with_logo_201(self, client, auth_headers):
        res = _create(client, auth_headers, nombre="ATM", logo_bytes=PNG_LOGO)
        assert res.status_code == 201
        assert res.json()["has_logo"] is True

    def test_create_rejects_empty_name_422(self, client, auth_headers):
        assert _create(client, auth_headers, nombre="   ").status_code == 422

    def test_create_rejects_bad_url_422(self, client, auth_headers):
        assert _create(client, auth_headers, url="javascript:alert(1)").status_code == 422
        assert _create(client, auth_headers, url="sin-esquema.com").status_code == 422

    def test_update_fields(self, client, auth_headers):
        cid = _create(client, auth_headers, nombre="Prudencia").json()["id"]
        res = client.put(f"/api/companies/admin/{cid}", json={
            "nombre": "Prudencia Seguros",
            "url": "https://www.prudencia.com.ar",
            "orden": 3,
        }, headers=auth_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["nombre"] == "Prudencia Seguros"
        assert body["url"] == "https://www.prudencia.com.ar"
        assert body["orden"] == 3

    def test_update_rejects_bad_url_422(self, client, auth_headers):
        cid = _create(client, auth_headers).json()["id"]
        res = client.put(f"/api/companies/admin/{cid}", json={"url": "no-es-url"}, headers=auth_headers)
        assert res.status_code == 422

    def test_update_nonexistent_404(self, client, auth_headers):
        res = client.put("/api/companies/admin/999", json={"nombre": "X"}, headers=auth_headers)
        assert res.status_code == 404

    def test_logo_upload_and_replace(self, client, auth_headers):
        cid = _create(client, auth_headers, nombre="Life").json()["id"]
        # upload onto a company created without logo
        res = client.put(f"/api/companies/admin/{cid}/logo",
                         files={"logo": ("l.png", PNG_LOGO, "image/png")}, headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["has_logo"] is True
        # replace with a JPEG
        res = client.put(f"/api/companies/admin/{cid}/logo",
                         files={"logo": ("l.jpg", JPG_LOGO, "image/jpeg")}, headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["logo_content_type"] == "image/jpeg"
        assert client.get(f"/api/companies/{cid}/logo").content == JPG_LOGO

    def test_logo_removal(self, client, auth_headers):
        cid = _create(client, auth_headers, logo_bytes=PNG_LOGO).json()["id"]
        res = client.delete(f"/api/companies/admin/{cid}/logo", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["has_logo"] is False
        assert client.get(f"/api/companies/{cid}/logo").status_code == 404

    def test_logo_rejects_svg_and_odd_types_422(self, client, auth_headers):
        cid = _create(client, auth_headers).json()["id"]
        # SVG: stored-XSS vector, always rejected
        svg = b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>"
        r1 = client.put(f"/api/companies/admin/{cid}/logo",
                        files={"logo": ("l.svg", svg, "image/svg+xml")}, headers=auth_headers)
        assert r1.status_code == 422
        # non-image
        r2 = client.put(f"/api/companies/admin/{cid}/logo",
                        files={"logo": ("l.exe", b"MZ...", "application/octet-stream")}, headers=auth_headers)
        assert r2.status_code == 422

    def test_logo_over_1mb_413(self, client, auth_headers):
        cid = _create(client, auth_headers).json()["id"]
        big = b"\x89PNG\r\n\x1a\n" + b"A" * (1 * 1024 * 1024)
        res = client.put(f"/api/companies/admin/{cid}/logo",
                         files={"logo": ("big.png", big, "image/png")}, headers=auth_headers)
        assert res.status_code == 413

    def test_logo_accepted_by_extension_with_odd_content_type(self, client, auth_headers):
        cid = _create(client, auth_headers).json()["id"]
        res = client.put(f"/api/companies/admin/{cid}/logo",
                         files={"logo": ("l.PNG", PNG_LOGO, "application/octet-stream")}, headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["logo_content_type"] == "image/png"

    def test_delete_company(self, client, auth_headers):
        cid = _create(client, auth_headers, nombre="Nación").json()["id"]
        res = client.delete(f"/api/companies/admin/{cid}", headers=auth_headers)
        assert res.status_code == 200
        assert client.get(f"/api/companies/admin", headers=auth_headers).json() == []
        assert client.delete(f"/api/companies/admin/{cid}", headers=auth_headers).status_code == 404


class TestBackupIntegration:
    def test_export_includes_companies(self, client, auth_headers):
        _create(client, auth_headers, nombre="BBVA", orden=7, logo_bytes=PNG_LOGO)
        b = client.get("/api/admin/backup/export", headers=auth_headers).json()
        assert b["meta"]["counts"]["companies"] == 1
        assert len(b["companies"]) == 1
        c = b["companies"][0]
        assert c["nombre"] == "BBVA"
        # the logo binary travels as base64 in the backup file
        assert c["logo_base64"] and isinstance(c["logo_base64"], str)
        assert "logo" not in c  # raw binary never inlined

    def test_summary_counts_companies(self, client, auth_headers):
        _create(client, auth_headers, nombre="Nación")
        s = client.get("/api/admin/backup/summary", headers=auth_headers).json()
        assert s["companies"] == 1

    def test_restore_roundtrip_preserves_companies(self, client, auth_headers):
        cid = _create(client, auth_headers, nombre="Credito y Caucion", orden=8,
                      logo_bytes=PNG_LOGO).json()["id"]
        backup = client.get("/api/admin/backup/export", headers=auth_headers).json()

        # mutate after export: extra company
        _create(client, auth_headers, nombre="Extra", orden=99)

        res = client.post("/api/admin/backup/restore", json=backup, headers=auth_headers)
        assert res.status_code == 200, res.text
        assert res.json()["restored"]["companies"] == 1

        companies = client.get("/api/companies/admin", headers=auth_headers).json()
        assert [c["nombre"] for c in companies] == ["Credito y Caucion"]
        assert companies[0]["id"] == cid
        # logo binary is empty until phase 2 restore
        assert companies[0]["has_logo"] is False
        assert client.get(f"/api/companies/{cid}/logo").status_code == 404

        # phase 2: logo restore via the upload endpoint → identical bytes
        r = client.put(f"/api/companies/admin/{cid}/logo",
                       files={"logo": ("logo.png", PNG_LOGO, "image/png")}, headers=auth_headers)
        assert r.status_code == 200
        assert client.get(f"/api/companies/{cid}/logo").content == PNG_LOGO

    def test_sequence_resync_after_restore(self, client, auth_headers):
        _create(client, auth_headers, nombre="A", orden=1)
        _create(client, auth_headers, nombre="B", orden=2)
        backup = client.get("/api/admin/backup/export", headers=auth_headers).json()

        # new rows after export push the sequence past the backup ids
        _create(client, auth_headers, nombre="C", orden=3)

        assert client.post("/api/admin/backup/restore", json=backup, headers=auth_headers).status_code == 200
        new = _create(client, auth_headers, nombre="D", orden=4).json()
        assert new["id"] > max(c["id"] for c in backup["companies"])
