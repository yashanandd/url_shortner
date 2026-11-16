import re
import secrets
import string

BASE62_ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase
DEFAULT_CODE_LENGTH = 7
ALIAS_REGEX = re.compile(r"^[a-zA-Z0-9_-]{3,30}$")


def generate_short_code(length: int = DEFAULT_CODE_LENGTH) -> str:
    """Generate a cryptographically secure random Base62 string."""
    return "".join(secrets.choice(BASE62_ALPHABET) for _ in range(length))


def is_valid_custom_alias(alias: str) -> bool:
    """Validate that custom alias meets length and character restrictions."""
    return bool(ALIAS_REGEX.match(alias))
