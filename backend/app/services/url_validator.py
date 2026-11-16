import ipaddress
import socket
from urllib.parse import urlparse
from app.core.config import settings

RESERVED_ROUTES = {
    "api",
    "auth",
    "login",
    "register",
    "logout",
    "dashboard",
    "admin",
    "health",
    "docs",
    "redoc",
    "openapi.json",
    "static",
    "favicon.ico",
    "analytics",
    "urls",
    "settings",
    "terms",
    "privacy",
    "about",
    "help",
    "status",
    "metrics",
}


class ValidationError(Exception):
    """Custom validation exception."""
    pass


def is_reserved_code(code: str) -> bool:
    """Check if the short code or alias conflicts with reserved application routes."""
    return code.lower().strip() in RESERVED_ROUTES


def _is_restricted_ip(ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Check if an IP address belongs to private, loopback, link-local, or reserved blocks."""
    return (
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_link_local
        or ip_obj.is_reserved
        or ip_obj.is_multicast
        or ip_obj.is_unspecified
    )


def validate_destination_url(url: str, check_dns: bool = None) -> str:
    """
    Validate destination URL:
    - Scheme must be http or https
    - Hostname must be present and not self-referential
    - Must not resolve to private, loopback, or reserved IP ranges (SSRF protection)
    """
    if check_dns is None:
        check_dns = settings.SSRF_CHECK_DNS

    cleaned_url = url.strip()
    if not cleaned_url:
        raise ValidationError("URL cannot be empty.")

    try:
        parsed = urlparse(cleaned_url)
    except Exception as e:
        raise ValidationError(f"Invalid URL structure: {e}")

    if parsed.scheme.lower() not in ("http", "https"):
        raise ValidationError("URL scheme must be HTTP or HTTPS.")

    hostname = parsed.hostname
    if not hostname:
        raise ValidationError("URL must contain a valid domain or host.")

    # Prevent circular redirects to LinkFlow itself
    app_base_parsed = urlparse(settings.BASE_URL)
    if app_base_parsed.hostname and hostname.lower() == app_base_parsed.hostname.lower():
        raise ValidationError("Destination cannot be a LinkFlow internal domain.")

    # 1. Direct IP literal check (works without DNS)
    try:
        ip_literal = ipaddress.ip_address(hostname)
        if _is_restricted_ip(ip_literal):
            raise ValidationError(
                f"Destination IP ({hostname}) resolves to a restricted private or loopback network."
            )
        return cleaned_url
    except ValueError:
        # Hostname is a domain name, not an IP literal
        pass

    # 2. SSRF Protection via DNS resolution (if enabled)
    if check_dns:
        try:
            addr_infos = socket.getaddrinfo(hostname, None)
            for addr_info in addr_infos:
                ip_str = addr_info[4][0]
                ip_obj = ipaddress.ip_address(ip_str)
                if _is_restricted_ip(ip_obj):
                    raise ValidationError(
                        f"Destination IP ({ip_str}) resolves to a restricted private or loopback network."
                    )
        except socket.gaierror:
            raise ValidationError(f"Could not resolve destination host '{hostname}'.")
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"SSRF validation check failed: {e}")

    return cleaned_url
