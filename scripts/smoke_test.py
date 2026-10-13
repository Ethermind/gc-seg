"""
Giaconi-Capra® PAS — Smoke Test E2E (sin dependencias externas)

Corre los flujos críticos de la API contra una base SQLite descartable:
login/JWT, creación de FAQ, creación de cobertura, subida y descarga
byte-idéntica de un manual PDF, y listados públicos.

Uso:
    python scripts/smoke_test.py            (con el venv del proyecto activo)

El CI (.github/workflows/smoke.yml) lo ejecuta instalando requirements.txt
en limpio: si una dependencia recién publicada rompe compatibilidad, el job
falla y el commit queda marcado en rojo ANTES de que Vercel despliegue.
"""
import os
import platform
import sys
import tempfile

# DB descartable: va ANTES de importar la app (el engine se crea al importar).
_tmpdir = tempfile.mkdtemp(prefix="gc-smoke-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir}/smoke.db"
os.environ.setdefault("ENVIRONMENT", "development")

# Asegurar que el path incluya la raíz del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def main() -> int:
    import sqlalchemy
    from fastapi.testclient import TestClient
    from api.index import app

    print(f"python={platform.python_version()} sqlalchemy={sqlalchemy.__version__}")

    c = TestClient(app)

    # 1. Setup del primer administrador
    r = c.post("/api/auth/setup", json={
        "username": "smokeadmin", "email": "smoke@test.dev",
        "password": "secret123", "full_name": "Smoke Test"
    })
    assert r.status_code == 201, f"setup admin fallo: {r.status_code} {r.text}"
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("1. setup admin OK")

    # 2. Login con las credenciales recién creadas
    r = c.post("/api/auth/login", json={"username": "smokeadmin", "password": "secret123"})
    assert r.status_code == 200, f"login fallo: {r.status_code} {r.text}"
    print("2. login OK")

    # 3. Crear FAQ (doctest del flujo admin -> Postgres sequences)
    r = c.post("/api/faqs/admin", json={
        "pregunta": "Pregunta de smoke test", "respuesta": "Respuesta de smoke test",
        "categoria": "general", "orden": 999, "activo": True
    }, headers=headers)
    assert r.status_code == 201, f"crear FAQ fallo: {r.status_code} {r.text}"
    faq_id = r.json()["id"]
    print("3. crear FAQ OK, id =", faq_id)

    # 4. Una segunda FAQ inmediata (cubre el bug histórico de secuencias en PG)
    r = c.post("/api/faqs/admin", json={
        "pregunta": "Segunda pregunta de smoke test", "respuesta": "Otra respuesta",
        "categoria": "general", "orden": 1000, "activo": True
    }, headers=headers)
    assert r.status_code == 201, f"segunda FAQ fallo: {r.status_code} {r.text}"
    print("4. segunda FAQ consecutiva OK, id =", r.json()["id"])

    # 5. Crear cobertura
    r = c.post("/api/coverages/admin", json={
        "categoria": "personas", "titulo": "Cobertura Smoke",
        "icono": "car", "descripcion": "Smoke", "orden": 999, "activo": True
    }, headers=headers)
    assert r.status_code == 201, f"crear cobertura fallo: {r.status_code} {r.text}"
    print("5. crear cobertura OK, id =", r.json()["id"])

    # 6. Subir manual PDF (multipart, igual que el navegador)
    pdf = b"%PDF-1.4 smoke test fake pdf content"
    r = c.post(
        "/api/admin/manuals",
        files={"file": ("manual-smoke.pdf", pdf, "application/pdf")},
        data={"producto": "Auto", "titulo": "Manual Smoke"},
        headers=headers,
    )
    assert r.status_code == 201, f"subir manual fallo: {r.status_code} {r.text}"
    manual_id = r.json()["id"]
    print("6. subir manual OK, id =", manual_id)

    # 7. Descargar manual y verificar integridad del blob
    r = c.get(f"/api/manuals/{manual_id}/download")
    assert r.status_code == 200 and r.content == pdf, \
        f"download manual fallo: {r.status_code}, bytes={len(r.content)}"
    print("7. descargar manual OK (bytes identicos)")

    # 8. Listados públicos
    assert any(x["id"] == faq_id for x in c.get("/api/faqs").json()), "FAQ no visible en publico"
    assert any(x["titulo"] == "Cobertura Smoke" for x in c.get("/api/coverages").json()), "cobertura no visible"
    assert any(x["id"] == manual_id for x in c.get("/api/manuals").json()), "manual no visible"
    print("8. listados publicos OK")

    print("\n=== SMOKE TEST COMPLETO: TODOS LOS FLUJOS FUNCIONAN ===")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f"\nSMOKE TEST FALLO: {e}", file=sys.stderr)
        sys.exit(1)
