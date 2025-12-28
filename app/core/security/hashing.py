"""
Password hashing utilities.

Uses bcrypt directly (not passlib) to avoid initialization issues.
Implements a hybrid approach:
1. Primary: Plain bcrypt (best security, no pre-hashing)
2. Fallback: SHA-256 pre-hash for passwords >72 bytes (handles edge cases)

This approach:
- Uses bcrypt library directly (avoids passlib initialization issues)
- Prefers plain bcrypt for maximum security
- Falls back to pre-hash only when needed (>72 bytes)
- Supports legacy hashes (backward compatibility)

References:
- https://dev.to/abbyesmith/password-hashing-using-bcrypt-in-python-2i08
- https://stackoverflow.com/a (Co0olCat's solution)
- OWASP Password Storage Cheat Sheet
"""

import hashlib

import bcrypt

# Bcrypt configuration
_BCRYPT_ROUNDS = 12


def _sha256_hexdigest_bytes(password: str) -> bytes:
    """Pre-hash password with SHA-256 and return as hex-encoded bytes.

    This produces a fixed 64-byte output (under bcrypt's 72-byte limit).
    Only used as a fallback for very long passwords.
    """
    return hashlib.sha256(password.encode()).hexdigest().encode()


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Strategy:
    1. Try plain bcrypt first (best security)
    2. If password >72 bytes, pre-hash with SHA-256 then bcrypt

    Args:
        password: Plain text password to hash

    Returns:
        Bcrypt hash string (e.g., "$2b$12$...")

    Raises:
        ValueError: If password is empty or None
    """
    if not password:
        raise ValueError("Password cannot be empty")

    password_bytes = password.encode("utf-8")

    # If password is >72 bytes, pre-hash with SHA-256
    # This ensures we stay under bcrypt's limit while maintaining security
    if len(password_bytes) > 72:
        prehashed = _sha256_hexdigest_bytes(password)
        password_bytes = prehashed

    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)

    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a stored hash.

    Strategy:
    1. Try pre-hashed mode first (SHA-256 hexdigest -> bcrypt)
    2. Fall back to plain bcrypt (for standard passwords)

    This supports both:
    - New hashes (may use pre-hash for long passwords)
    - Legacy hashes (plain bcrypt)

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hash to verify against

    Returns:
        True if password matches, False otherwise
    """
    if not plain_password or not hashed_password:
        return False

    try:
        hp_bytes = hashed_password.encode("utf-8")
        password_bytes = plain_password.encode("utf-8")

        # 1) Try pre-hashed path first (for passwords that were >72 bytes)
        # This handles the case where password was pre-hashed during creation
        prehashed = _sha256_hexdigest_bytes(plain_password)
        if bcrypt.checkpw(prehashed, hp_bytes):
            return True

        # 2) Fallback: plain bcrypt (standard case, most passwords)
        # This handles normal passwords and legacy hashes
        if len(password_bytes) <= 72:
            return bcrypt.checkpw(password_bytes, hp_bytes)

        # 3) If password >72 bytes and pre-hash didn't match,
        # try plain (in case hash was created with plain >72 byte password)
        # Note: bcrypt v5+ may raise ValueError for >72 bytes
        try:
            return bcrypt.checkpw(password_bytes, hp_bytes)
        except ValueError:
            # bcrypt v5+ raises if input >72 bytes
            return False

    except (ValueError, TypeError):
        # Invalid hash format or other verification errors
        return False
