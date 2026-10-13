"""Tests for api.auth: bcrypt hashing and JWT (units, no DB)."""
from datetime import timedelta

from api.auth import (
    hash_password, verify_password, create_access_token, decode_access_token,
)


class TestPasswordHashing:
    def test_hash_is_not_plaintext_and_verifies(self):
        h = hash_password("mi-secreto")
        assert h != "mi-secreto"
        assert h.startswith("$2")
        assert verify_password("mi-secreto", h)

    def test_wrong_password_does_not_verify(self):
        h = hash_password("correct")
        assert not verify_password("incorrect", h)

    def test_two_hashes_of_same_password_differ_by_salt(self):
        assert hash_password("x") != hash_password("x")

    def test_password_over_72_bytes_does_not_explode(self):
        # Regression: bcrypt 5.x raised ValueError on >72 bytes; we truncate explicitly.
        long_pwd = "á" * 100  # 200 bytes in utf-8
        h = hash_password(long_pwd)
        assert verify_password(long_pwd, h)

    def test_verify_with_corrupt_hash_returns_false(self):
        assert not verify_password("x", "not-a-bcrypt-hash")


class TestJWT:
    def test_token_contains_claims(self):
        token = create_access_token({"sub": "admin", "role": "superadmin", "uid": 7})
        payload = decode_access_token(token)
        assert payload["sub"] == "admin"
        assert payload["role"] == "superadmin"
        assert payload["uid"] == 7
        assert "exp" in payload

    def test_expired_token_returns_none(self):
        token = create_access_token({"sub": "admin"}, expires_delta=timedelta(seconds=-10))
        assert decode_access_token(token) is None

    def test_garbage_token_returns_none(self):
        assert decode_access_token("garbage.token.haha") is None

    def test_token_signed_with_wrong_secret_returns_none(self):
        import jwt as pyjwt
        from datetime import datetime, timezone
        token = pyjwt.encode(
            {"sub": "admin", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
            "some-other-secret-key-that-is-long-enough",
            algorithm="HS256",
        )
        assert decode_access_token(token) is None
