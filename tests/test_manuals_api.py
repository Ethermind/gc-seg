"""Tests for Manual PDF endpoints (admin: upload/delete; public: list/download)."""

PDF_OK = b"%PDF-1.4 fake pdf content"
MAX = 4 * 1024 * 1024  # same limit as api.routes.admin


def _upload(client, headers, file_bytes=PDF_OK, filename="manual.pdf", content_type="application/pdf",
            producto="Auto", titulo="Manual de Auto"):
    return client.post(
        "/api/admin/manuals",
        files={"file": (filename, file_bytes, content_type)},
        data={"producto": producto, "titulo": titulo},
        headers=headers,
    )


class TestManualUploadValidations:
    def test_successful_upload_201(self, client, auth_headers):
        r = _upload(client, auth_headers)
        assert r.status_code == 201
        body = r.json()
        assert body["size_bytes"] == len(PDF_OK)
        assert body["content_type"] == "application/pdf"

    def test_non_pdf_422(self, client, auth_headers):
        r = _upload(client, auth_headers, file_bytes=b"hi", filename="photo.png", content_type="image/png")
        assert r.status_code == 422

    def test_empty_file_422(self, client, auth_headers):
        r = _upload(client, auth_headers, file_bytes=b"")
        assert r.status_code == 422

    def test_pdf_extension_with_odd_content_type_is_accepted(self, client, auth_headers):
        r = _upload(client, auth_headers, filename="manual.PDF", content_type="application/octet-stream")
        assert r.status_code == 201

    def test_over_4mb_413(self, client, auth_headers):
        r = _upload(client, auth_headers, file_bytes=b"%PDF" + b"A" * MAX)
        assert r.status_code == 413

    def test_empty_title_422(self, client, auth_headers):
        r = _upload(client, auth_headers, titulo="   ")
        assert r.status_code == 422

    def test_empty_product_422(self, client, auth_headers):
        r = _upload(client, auth_headers, producto=" ")
        assert r.status_code == 422

    def test_without_token_is_rejected(self, client):
        r = client.post(
            "/api/admin/manuals",
            files={"file": ("m.pdf", PDF_OK, "application/pdf")},
            data={"producto": "Auto", "titulo": "X"},
        )
        assert r.status_code in (401, 403)


class TestManualDownloadAndListing:
    def test_download_identical_bytes_and_headers(self, client, auth_headers):
        mid = _upload(client, auth_headers, filename="mi manual raro?.pdf").json()["id"]
        r = client.get(f"/api/manuals/{mid}/download")
        assert r.status_code == 200
        assert r.content == PDF_OK
        assert r.headers["content-type"] == "application/pdf"
        cd = r.headers["content-disposition"]
        assert "inline" in cd and ".pdf" in cd
        # sanitized filename: no spaces or weird characters
        import re
        name = re.search(r'filename="([^"]+)"', cd).group(1)
        assert re.fullmatch(r"[A-Za-z0-9_.\-]+", name)

    def test_download_nonexistent_404(self, client):
        assert client.get("/api/manuals/9999/download").status_code == 404

    def test_public_listing_and_filter_by_product(self, client, auth_headers):
        _upload(client, auth_headers, producto="Auto", titulo="Manual Auto")
        _upload(client, auth_headers, producto="Moto", titulo="Manual Moto")
        assert len(client.get("/api/manuals").json()) == 2
        r = client.get("/api/manuals?producto=Moto")
        assert [m["titulo"] for m in r.json()] == ["Manual Moto"]

    def test_delete(self, client, auth_headers):
        mid = _upload(client, auth_headers).json()["id"]
        assert client.delete(f"/api/admin/manuals/{mid}", headers=auth_headers).status_code == 200
        assert client.get(f"/api/manuals/{mid}/download").status_code == 404
