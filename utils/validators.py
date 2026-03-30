"""
Input Validation — Path Traversal Protection, Size Limits, Format Checks

Centralized validation for all user-supplied inputs to prevent:
- Path traversal attacks
- Denial of service via oversized files
- Injection via malformed domain names
"""

import re
from pathlib import Path
from typing import Optional


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


# ─────────────────────────────────────────────────────────────
# File Path Validation
# ─────────────────────────────────────────────────────────────

def validate_file_path(
    file_path: str,
    allowed_root: Optional[str] = None,
    max_size_mb: float = 100.0,
    allowed_extensions: Optional[list] = None,
) -> Path:
    """
    Validate and sanitize a file path input.

    Args:
        file_path: User-supplied file path
        allowed_root: If set, the file must be under this directory
        max_size_mb: Maximum allowed file size in MB
        allowed_extensions: List of allowed extensions (e.g., ['.exe', '.dll'])

    Returns:
        Resolved Path object

    Raises:
        ValidationError: If validation fails
    """
    if not file_path or not file_path.strip():
        raise ValidationError("File path cannot be empty")

    path = Path(file_path).resolve()

    # Path traversal check
    if allowed_root:
        root = Path(allowed_root).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            raise ValidationError(
                f"Path traversal detected: {file_path} is outside allowed root"
            )

    # Existence check
    if not path.exists():
        raise ValidationError(f"File not found: {path}")

    if not path.is_file():
        raise ValidationError(f"Not a file: {path}")

    # Size check
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ValidationError(
            f"File too large: {size_mb:.1f} MB > {max_size_mb} MB limit"
        )

    # Extension check
    if allowed_extensions:
        if path.suffix.lower() not in [e.lower() for e in allowed_extensions]:
            raise ValidationError(
                f"Unsupported file type: {path.suffix}. "
                f"Allowed: {', '.join(allowed_extensions)}"
            )

    return path


def validate_directory_path(
    dir_path: str,
    allowed_root: Optional[str] = None,
) -> Path:
    """
    Validate and sanitize a directory path.

    Args:
        dir_path: User-supplied directory path
        allowed_root: If set, the directory must be under this root

    Returns:
        Resolved Path object

    Raises:
        ValidationError: If validation fails
    """
    if not dir_path or not dir_path.strip():
        raise ValidationError("Directory path cannot be empty")

    path = Path(dir_path).resolve()

    if allowed_root:
        root = Path(allowed_root).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            raise ValidationError(
                f"Path traversal detected: {dir_path} is outside allowed root"
            )

    if not path.exists():
        raise ValidationError(f"Directory not found: {path}")

    if not path.is_dir():
        raise ValidationError(f"Not a directory: {path}")

    return path


# ─────────────────────────────────────────────────────────────
# Domain Validation
# ─────────────────────────────────────────────────────────────

# RFC-compliant domain pattern
_DOMAIN_PATTERN = re.compile(
    r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*'
    r'[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$'
)

_URL_PREFIX = re.compile(r'^https?://')


def validate_domain(domain: str) -> str:
    """
    Validate and sanitize a domain name or URL input.

    Args:
        domain: User-supplied domain name or URL

    Returns:
        Cleaned domain string

    Raises:
        ValidationError: If validation fails
    """
    if not domain or not domain.strip():
        raise ValidationError("Domain cannot be empty")

    domain = domain.strip()

    # Strip protocol if URL
    if _URL_PREFIX.match(domain):
        domain = _URL_PREFIX.sub('', domain)
        domain = domain.split('/')[0]
        domain = domain.split(':')[0]

    # Length check
    if len(domain) > 253:
        raise ValidationError(
            f"Domain too long: {len(domain)} chars (max 253)"
        )

    # Character validation
    if not _DOMAIN_PATTERN.match(domain):
        # Allow IP addresses
        if not _is_valid_ip(domain):
            raise ValidationError(
                f"Invalid domain format: {domain}"
            )

    return domain


def _is_valid_ip(text: str) -> bool:
    """Check if text is a valid IPv4 address."""
    parts = text.split('.')
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False


# ─────────────────────────────────────────────────────────────
# Hash Validation
# ─────────────────────────────────────────────────────────────

_HASH_PATTERNS = {
    'md5': re.compile(r'^[a-fA-F0-9]{32}$'),
    'sha1': re.compile(r'^[a-fA-F0-9]{40}$'),
    'sha256': re.compile(r'^[a-fA-F0-9]{64}$'),
}


def validate_hash(hash_value: str, hash_type: str = 'auto') -> str:
    """
    Validate a file hash string.

    Args:
        hash_value: The hash string to validate
        hash_type: 'md5', 'sha1', 'sha256', or 'auto' (detect by length)

    Returns:
        Lowercased hash string

    Raises:
        ValidationError: If hash format is invalid
    """
    if not hash_value or not hash_value.strip():
        raise ValidationError("Hash cannot be empty")

    hash_value = hash_value.strip().lower()

    if hash_type == 'auto':
        length = len(hash_value)
        if length == 32:
            hash_type = 'md5'
        elif length == 40:
            hash_type = 'sha1'
        elif length == 64:
            hash_type = 'sha256'
        else:
            raise ValidationError(
                f"Cannot auto-detect hash type for length {length}"
            )

    if hash_type not in _HASH_PATTERNS:
        raise ValidationError(f"Unknown hash type: {hash_type}")

    if not _HASH_PATTERNS[hash_type].match(hash_value):
        raise ValidationError(
            f"Invalid {hash_type.upper()} hash format: {hash_value}"
        )

    return hash_value
