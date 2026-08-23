from datetime import datetime, timedelta, timezone

import pytest
from jose import JWTError, jwt

from app.core import security
from app.core.config import settings


def test_hash_and_verify_password_roundtrip():
    plain = "supersecret123"
    hashed = security.hash_password(plain)

    assert hashed != plain
    assert security.verify_password(plain, hashed) is True
    assert security.verify_password("wrong-password", hashed) is False


def test_create_and_decode_token_roundtrip():
    token = security.create_access_token(subject=42)

    payload = security.decode_access_token(token)

    assert payload["sub"] == "42"
    assert "exp" in payload
    assert set(payload.keys()) == {"sub", "exp"}


def test_decode_expired_token_raises():
    expired_token = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
        },
        settings.JWT_SECRET,
        algorithm="HS256",
    )

    with pytest.raises(JWTError):
        security.decode_access_token(expired_token)


def test_decode_token_wrong_algorithm_is_rejected():
    token_signed_hs512 = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        settings.JWT_SECRET,
        algorithm="HS512",
    )

    with pytest.raises(JWTError):
        security.decode_access_token(token_signed_hs512)
