"""Tests for admin backup/restore endpoints (export, restore, manual binaries)."""

PDF_A = b"%PDF-1.4 backup pdf A"
PDF_B = b"%PDF-1.4 backup pdf B with different content"


def _upload_manual(client, headers, producto="Auto", titulo="Manual Auto",
                   file_bytes=PDF_A, filename="manual.pdf"):
    return client.post(
        "/api/admin/manuals",
        files={"file": (filename, file_bytes, "application/pdf")},
        data={"producto": producto, "titulo": titulo},
        headers=headers,
    )


def _export(client, headers):
    r = client.get("/api/admin/backup/export", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def _restore(client, headers, backup):
    return client.post("/api/admin/backup/restore", json=backup, headers=headers)


def _create_admin(client, headers, username, role="admin"):
    r = client.post("/api/admin/users", json={
        "username": username,
        "email": f"{username}@test.dev",
        "password": "secret123",
        "full_name": f"{username} Test",
        "role": role,
    }, headers=headers)
    assert r.status_code == 201, r.text
    login = client.post("/api/auth/login", json={"username": username, "password": "secret123"})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


class TestBackupSummaryAndExport:
    def test_export_requires_auth(self, client):
        assert client.get("/api/admin/backup/export").status_code in (401, 403)

    def test_summary_requires_auth(self, client):
        assert client.get("/api/admin/backup/summary").status_code in (401, 403)

    def test_summary_counts(self, client, auth_headers):
        _upload_manual(client, auth_headers)
        client.post("/api/admin/leads", json={
            "nombre": "Juan Pérez", "telefono": "2664551234",
        }, headers=auth_headers)
        s = client.get("/api/admin/backup/summary", headers=auth_headers).json()
        assert s["manuals"] == 1
        assert s["leads"] == 1
        assert s["manuals_total_bytes"] == len(PDF_A)
        assert s["admin_users"] == 1

    def test_export_shape_and_manual_metadata_only(self, client, auth_headers):
        _upload_manual(client, auth_headers, producto="Auto", titulo="T1")
        b = _export(client, auth_headers)
        assert b["meta"]["app"] == "gc-seg"
        assert b["meta"]["version"] == 1
        assert b["meta"]["counts"]["manuals"] == 1
        assert "exported_at" in b["meta"]
        m = b["manuals"][0]
        assert m["titulo"] == "T1"
        assert m["size_bytes"] == len(PDF_A)
        # Binaries are never embedded in the metadata export
        assert "data" not in m and "data_base64" not in m
        for key in ("coverages", "faqs", "reviews", "leads", "admin_users", "manuals"):
            assert key in b


class TestBackupRestoreValidations:
    def test_restore_requires_auth(self, client):
        r = client.post("/api/admin/backup/restore", json={"meta": {"app": "gc-seg", "version": 1, "exported_at": "x"}})
        assert r.status_code in (401, 403)

    def test_restore_requires_superadmin(self, client, auth_headers):
        _create_admin(client, auth_headers, "plainadmin")
        backup = _export(client, auth_headers)
        plain = _create_admin(client, auth_headers, "secondadmin")
        # reuse a valid backup exported by the superadmin
        r = _restore(client, plain, backup)
        assert r.status_code == 403

    def test_restore_rejects_other_app(self, client, auth_headers):
        backup = _export(client, auth_headers)
        backup["meta"]["app"] = "otro-sitio"
        assert _restore(client, auth_headers, backup).status_code == 422

    def test_restore_rejects_newer_version(self, client, auth_headers):
        backup = _export(client, auth_headers)
        backup["meta"]["version"] = 999
        assert _restore(client, auth_headers, backup).status_code == 422

    def test_restore_rejects_invalid_lead_status(self, client, auth_headers):
        backup = _export(client, auth_headers)
        backup["leads"] = [{"id": 1, "nombre": "X", "telefono": "123456",
                            "status": "estado_inventado"}]
        r = _restore(client, auth_headers, backup)
        assert r.status_code == 422


class TestBackupRestoreData:
    def test_manuals_roundtrip_preserves_ids_and_resyncs_sequence(self, client, auth_headers):
        _upload_manual(client, auth_headers, producto="Auto", titulo="Manual A")
        _upload_manual(client, auth_headers, producto="Moto", titulo="Manual B")
        backup = _export(client, auth_headers)

        # Mutate the live DB after exporting
        _upload_manual(client, auth_headers, producto="Extra", titulo="Extra")

        r = _restore(client, auth_headers, backup)
        assert r.status_code == 200, r.text
        assert r.json()["restored"]["manuals"] == 2

        manuals = client.get("/api/manuals", headers=auth_headers).json()
        assert sorted(m["id"] for m in manuals) == sorted(m["id"] for m in backup["manuals"])

        # Sequence resync: next insert does not collide with restored ids
        new = _upload_manual(client, auth_headers, producto="Post", titulo="Post").json()
        assert new["id"] > max(m["id"] for m in backup["manuals"])

    def test_leads_roundtrip(self, client, auth_headers):
        client.post("/api/admin/leads", json={
            "nombre": "Juan Pérez", "telefono": "2664551234",
            "email": "juan@test.dev", "producto": "Auto", "mensaje": "Hola",
        }, headers=auth_headers)
        backup = _export(client, auth_headers)

        client.post("/api/admin/leads", json={
            "nombre": "Otro Lead", "telefono": "2664559999",
        }, headers=auth_headers)

        assert _restore(client, auth_headers, backup).status_code == 200
        leads = client.get("/api/admin/leads", headers=auth_headers).json()
        assert [l["id"] for l in leads] == [l["id"] for l in backup["leads"]]
        assert [l["nombre"] for l in leads] == [l["nombre"] for l in backup["leads"]]

    def test_coverages_and_faqs_roundtrip(self, client, auth_headers):
        cov = client.post("/api/coverages/admin", json={
            "categoria": "personas", "titulo": "Auto Cobertura", "icono": "car",
            "descripcion": "Desc", "orden": 1,
        }, headers=auth_headers)
        assert cov.status_code == 201, cov.text
        faq = client.post("/api/faqs/admin", json={
            "pregunta": "¿Qué es?", "respuesta": "Es una prueba", "orden": 1,
        }, headers=auth_headers)
        assert faq.status_code == 201, faq.text
        backup = _export(client, auth_headers)

        # mutate after export
        client.post("/api/coverages/admin", json={
            "categoria": "empresas", "titulo": "Extra", "icono": "building",
            "descripcion": "Extra", "orden": 2,
        }, headers=auth_headers)

        assert _restore(client, auth_headers, backup).status_code == 200
        coverages = client.get("/api/coverages").json()
        faqs = client.get("/api/faqs").json()
        assert [c["titulo"] for c in coverages] == ["Auto Cobertura"]
        assert [f["pregunta"] for f in faqs] == ["¿Qué es?"]
        assert coverages[0]["id"] == backup["coverages"][0]["id"]


class TestBackupRestoreAdminUsers:
    def test_operator_survives_and_admins_synced(self, client, auth_headers):
        backup = _export(client, auth_headers)  # contains only the operator
        _create_admin(client, auth_headers, "tempadmin")  # created AFTER backup

        assert _restore(client, auth_headers, backup).status_code == 200
        users = client.get("/api/admin/users", headers=auth_headers).json()
        usernames = {u["username"] for u in users}
        assert "tempadmin" not in usernames          # removed: not in backup
        assert "superadmin" in usernames             # operator survives
        assert client.get("/api/auth/me", headers=auth_headers).status_code == 200

    def test_operator_survives_backup_without_admins(self, client, auth_headers):
        backup = _export(client, auth_headers)
        backup["admin_users"] = []                    # operator not in backup
        assert _restore(client, auth_headers, backup).status_code == 200
        assert client.get("/api/auth/me", headers=auth_headers).status_code == 200
        users = client.get("/api/admin/users", headers=auth_headers).json()
        assert [u["username"] for u in users] == ["superadmin"]

    def test_admin_upserted_from_backup(self, client, auth_headers):
        backup = _export(client, auth_headers)
        backup["admin_users"][0]["full_name"] = "Nombre Restaurado"
        assert _restore(client, auth_headers, backup).status_code == 200
        me = client.get("/api/auth/me", headers=auth_headers).json()
        assert me["full_name"] == "Nombre Restaurado"


class TestBackupRestoreManualBinaries:
    def test_binary_restore_roundtrip_identical_bytes(self, client, auth_headers):
        _upload_manual(client, auth_headers, file_bytes=PDF_A, filename="a.pdf")
        backup = _export(client, auth_headers)
        mid = backup["manuals"][0]["id"]

        assert _restore(client, auth_headers, backup).status_code == 200
        # phase 2: binary upload
        r = client.post(
            f"/api/admin/backup/restore/manuals/{mid}",
            files={"file": ("a.pdf", PDF_A, "application/pdf")},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        assert r.json()["size_bytes"] == len(PDF_A)

        dl = client.get(f"/api/manuals/{mid}/download")
        assert dl.status_code == 200 and dl.content == PDF_A

    def test_binary_restore_404_without_metadata_restore(self, client, auth_headers):
        r = client.post(
            "/api/admin/backup/restore/manuals/999",
            files={"file": ("m.pdf", PDF_A, "application/pdf")},
            headers=auth_headers,
        )
        assert r.status_code == 404

    def test_binary_restore_rejects_non_pdf(self, client, auth_headers):
        _upload_manual(client, auth_headers)
        backup = _export(client, auth_headers)
        assert _restore(client, auth_headers, backup).status_code == 200
        mid = backup["manuals"][0]["id"]
        r = client.post(
            f"/api/admin/backup/restore/manuals/{mid}",
            files={"file": ("x.png", b"hi", "image/png")},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_binary_restore_rejects_oversize(self, client, auth_headers):
        _upload_manual(client, auth_headers)
        backup = _export(client, auth_headers)
        assert _restore(client, auth_headers, backup).status_code == 200
        mid = backup["manuals"][0]["id"]
        big = b"%PDF" + b"A" * (4 * 1024 * 1024)
        r = client.post(
            f"/api/admin/backup/restore/manuals/{mid}",
            files={"file": ("big.pdf", big, "application/pdf")},
            headers=auth_headers,
        )
        assert r.status_code == 413
