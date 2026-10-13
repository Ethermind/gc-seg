"""
Giaconi-Capra® PAS — Dependency-free E2E smoke test.

Runs the critical API flows against a throwaway SQLite database:
login/JWT, FAQ creation, coverage creation, upload and byte-identical
download of a PDF manual, and the public listings.

Usage:
    python scripts/smoke_test.py            (with the project venv active)

CI (.github/workflows/smoke.yml) executes it after installing
requirements.txt from scratch: if a freshly published dependency breaks
compatibility, the job fails and the commit is marked red BEFORE Vercel
finishes deploying.
"""
import os
import platform
import sys
import tempfile

# Throwaway DB: must be set BEFORE importing the app (engine is created at import).
_tmpdir = tempfile.mkdtemp(prefix="gc-smoke-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir}/smoke.db"
os.environ.setdefault("ENVIRONMENT", "development")

# Ensure the path includes the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def main() -> int:
    import sqlalchemy
    from fastapi.testclient import TestClient
    from api.index import app

    print(f"python={platform.python_version()} sqlalchemy={sqlalchemy.__version__}")

    c = TestClient(app)

    # 1. Initial admin setup
    r = c.post("/api/auth/setup", json={
        "username": "smokeadmin", "email": "smoke@test.dev",
        "password": "secret123", "full_name": "Smoke Test"
    })
    assert r.status_code == 201, f"admin setup failed: {r.status_code} {r.text}"
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("1. admin setup OK")

    # 2. Login with the newly created credentials
    r = c.post("/api/auth/login", json={"username": "smokeadmin", "password": "secret123"})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    print("2. login OK")

    # 3. Create a FAQ (smoke-doctest of the admin -> DB sequence flow)
    r = c.post("/api/faqs/admin", json={
        "pregunta": "Pregunta de smoke test", "respuesta": "Respuesta de smoke test",
        "categoria": "general", "orden": 999, "activo": True
    }, headers=headers)
    assert r.status_code == 201, f"FAQ creation failed: {r.status_code} {r.text}"
    faq_id = r.json()["id"]
    print("3. FAQ created OK, id =", faq_id)

    # 4. A second FAQ right after (covers the historical PG sequence bug)
    r = c.post("/api/faqs/admin", json={
        "pregunta": "Segunda pregunta de smoke test", "respuesta": "Otra respuesta",
        "categoria": "general", "orden": 1000, "activo": True
    }, headers=headers)
    assert r.status_code == 201, f"second FAQ failed: {r.status_code} {r.text}"
    print("4. second consecutive FAQ OK, id =", r.json()["id"])

    # 5. Create a coverage
    r = c.post("/api/coverages/admin", json={
        "categoria": "personas", "titulo": "Cobertura Smoke",
        "icono": "car", "descripcion": "Smoke", "orden": 999, "activo": True
    }, headers=headers)
    assert r.status_code == 201, f"coverage creation failed: {r.status_code} {r.text}"
    print("5. coverage created OK, id =", r.json()["id"])

    # 6. Upload a PDF manual (multipart, same as the browser)
    pdf = b"%PDF-1.4 smoke test fake pdf content"
    r = c.post(
        "/api/admin/manuals",
        files={"file": ("manual-smoke.pdf", pdf, "application/pdf")},
        data={"producto": "Auto", "titulo": "Manual Smoke"},
        headers=headers,
    )
    assert r.status_code == 201, f"manual upload failed: {r.status_code} {r.text}"
    manual_id = r.json()["id"]
    print("6. manual uploaded OK, id =", manual_id)

    # 7. Download the manual and verify blob integrity
    r = c.get(f"/api/manuals/{manual_id}/download")
    assert r.status_code == 200 and r.content == pdf, \
        f"manual download failed: {r.status_code}, bytes={len(r.content)}"
    print("7. manual downloaded OK (identical bytes)")

    # 8. Public listings
    assert any(x["id"] == faq_id for x in c.get("/api/faqs").json()), "FAQ not visible publicly"
    assert any(x["titulo"] == "Cobertura Smoke" for x in c.get("/api/coverages").json()), "coverage not visible"
    assert any(x["id"] == manual_id for x in c.get("/api/manuals").json()), "manual not visible"
    print("8. public listings OK")

    print("\n=== SMOKE TEST COMPLETE: ALL FLOWS WORK ===")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f"\nSMOKE TEST FAILED: {e}", file=sys.stderr)
        sys.exit(1)
