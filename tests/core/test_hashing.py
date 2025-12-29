"""Tests for password hashing functionality."""

import pytest

from app.core.security.hashing import hash_password, verify_password


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password(self):
        """Test hashing a password."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password
        assert hashed.startswith("$2")  # bcrypt hash prefix

    def test_verify_password_correct(self):
        """Test verifying a correct password."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying an incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_hash_password_different_outputs(self):
        """Test that hashing the same password produces different hashes."""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Bcrypt generates different salts, so hashes should differ
        assert hash1 != hash2

        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_verify_empty_password(self):
        """Test that empty passwords are rejected."""
        password = ""

        # Empty passwords should not be allowed
        with pytest.raises(ValueError, match="Password cannot be empty"):
            hash_password(password)

        # Verification should also return False for empty passwords
        # (even if we had a hash, which we shouldn't)
        fake_hash = "$2b$12$dummyhash"
        assert verify_password(password, fake_hash) is False
