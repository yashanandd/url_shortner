import pytest
from app.services.url_validator import (
    ValidationError,
    is_reserved_code,
    validate_destination_url,
)


def test_is_reserved_code():
    assert is_reserved_code("api") is True
    assert is_reserved_code("docs") is True
    assert is_reserved_code("LOGIN") is True
    assert is_reserved_code("my-portfolio") is False


def test_validate_destination_url_valid():
    url = "https://example.com/products/123"
    assert validate_destination_url(url, check_dns=False) == url


def test_validate_destination_url_invalid_scheme():
    with pytest.raises(ValidationError, match="scheme must be HTTP or HTTPS"):
        validate_destination_url("ftp://ftp.example.com/file.zip")

    with pytest.raises(ValidationError, match="scheme must be HTTP or HTTPS"):
        validate_destination_url("javascript:alert(1)")


def test_validate_destination_url_ssrf_loopback_ip():
    with pytest.raises(ValidationError, match="restricted private or loopback network"):
        validate_destination_url("http://127.0.0.1/admin")


def test_validate_destination_url_ssrf_private_ips():
    with pytest.raises(ValidationError, match="restricted private or loopback network"):
        validate_destination_url("http://10.0.0.1/secret")

    with pytest.raises(ValidationError, match="restricted private or loopback network"):
        validate_destination_url("http://192.168.1.100/config")


def test_validate_destination_url_circular_domain():
    with pytest.raises(ValidationError, match="LinkFlow internal domain"):
        validate_destination_url("http://localhost:8000/api")
