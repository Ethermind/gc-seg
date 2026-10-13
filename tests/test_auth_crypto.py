"""Tests de api.auth: hashing bcrypt y JWT (unidad, sin DB)."""
from datetime import timedelta

from api.auth import (
    hash_password, verify_password, create_access_token, decode_access_token,
)


class TestPasswordHashing:
    def test_hash_no_es_texto_plano_y_verifica(self):
        h = hash_password("mi-secreto")
        assert h != "mi-secreto"
        assert h.startswith("$2")
        assert verify_password("mi-secreto", h)

    def test_password_incorrecta_no_verifica(self):
        h = hash_password("correcta")
        assert not verify_password("incorrecta", h)

    def test_dos_hashes_de_lo_mismo_difieren_por_salt(self):
        assert hash_password("x") != hash_password("x")

    def test_password_mayor_a_72_bytes_no_explota(self):
        # Regresión bcrypt 5.x: >72 bytes lanzaba ValueError; se trunca explícito.
        larga = "á" * 100  # 200 bytes en utf-8
        h = hash_password(larga)
        assert verify_password(larga, h)

    def test_verify_con_hash_corrupto_devuelve_false(self):
        assert not verify_password("x", "no-es-un-hash-bcrypt")


class TestJWT:
    def test_token_contiene_claims(self):
        token = create_access_token({"sub": "admin", "role": "superadmin", "uid": 7})
        payload = decode_access_token(token)
        assert payload["sub"] == "admin"
        assert payload["role"] == "superadmin"
        assert payload["uid"] == 7
        assert "exp" in payload

    def test_token_expirado_devuelve_none(self):
        token = create_access_token({"sub": "admin"}, expires_delta=timedelta(seconds=-10))
        assert decode_access_token(token) is None

    def test_token_basura_devuelve_none(self):
        assert decode_access_token("token.inventado.jaja") is None

    def test_token_firmado_con_otra_clave_devuelve_none(self):
        import jwt as pyjwt
        from datetime import datetime, timezone
        token = pyjwt.encode(
            {"sub": "admin", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
            "otra-clave-cualquiera",
            algorithm="HS256",
        )
        assert decode_access_token(token) is None
