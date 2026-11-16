import pytest
from app.services.code_generator import generate_short_code, is_valid_custom_alias, BASE62_ALPHABET


def test_generate_short_code_length():
    code = generate_short_code(7)
    assert len(code) == 7
    assert all(c in BASE62_ALPHABET for c in code)


def test_generate_short_code_randomness():
    codes = {generate_short_code(7) for _ in range(100)}
    assert len(codes) == 100  # No collisions in 100 samples


def test_is_valid_custom_alias():
    assert is_valid_custom_alias("my-link") is True
    assert is_valid_custom_alias("demo_123") is True
    assert is_valid_custom_alias("aB92") is True
    assert is_valid_custom_alias("ab") is False  # Too short (<3)
    assert is_valid_custom_alias("a" * 31) is False  # Too long (>30)
    assert is_valid_custom_alias("invalid space") is False
    assert is_valid_custom_alias("invalid$char") is False
