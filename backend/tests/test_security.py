import pytest
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hashing():
    pw = "SuperSecretP@ssword123"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_tokens():
    data = {"sub": "user-uuid-123", "email": "test@example.com"}
    access = create_access_token(data)
    assert isinstance(access, str)

    decoded = decode_token(access)
    assert decoded["sub"] == "user-uuid-123"
    assert decoded["email"] == "test@example.com"
    assert decoded["type"] == "access"
    assert "jti" in decoded
    assert "exp" in decoded

    refresh = create_refresh_token(data)
    decoded_refresh = decode_token(refresh)
    assert decoded_refresh["type"] == "refresh"
    assert decoded_refresh["sub"] == "user-uuid-123"
