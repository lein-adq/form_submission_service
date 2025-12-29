"""Tests for JWT token functionality."""

import time
from uuid import uuid4

import pytest
from jose import jwt

from app.core.config.settings import settings
from app.core.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)


class TestJWT:
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        """Test creating an access token."""
        user_id = uuid4()
        email = "test@example.com"

        token = create_access_token(user_id, email)

        assert token is not None
        assert isinstance(token, str)

        # Decode and verify
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        assert payload["sub"] == str(user_id)
        assert payload["email"] == email
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        """Test creating a refresh token."""
        user_id = uuid4()
        email = "test@example.com"

        token = create_refresh_token(user_id, email)

        assert token is not None
        assert isinstance(token, str)

        # Decode and verify
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        assert payload["sub"] == str(user_id)
        assert payload["email"] == email
        assert payload["type"] == "refresh"

    def test_decode_access_token(self):
        """Test decoding an access token."""
        user_id = uuid4()
        email = "test@example.com"

        token = create_access_token(user_id, email)
        identity = decode_access_token(token)

        assert identity.user_id == user_id
        assert identity.email == email

    def test_decode_refresh_token(self):
        """Test decoding a refresh token."""
        user_id = uuid4()
        email = "test@example.com"

        token = create_refresh_token(user_id, email)
        identity = decode_refresh_token(token)

        assert identity.user_id == user_id
        assert identity.email == email

    def test_decode_invalid_token(self):
        """Test decoding an invalid token raises error."""
        with pytest.raises(ValueError, match="Invalid token"):
            decode_access_token("invalid-token")

    def test_decode_wrong_token_type(self):
        """Test decoding wrong token type raises error."""
        user_id = uuid4()
        email = "test@example.com"

        # Create refresh token but try to decode as access token
        refresh_token = create_refresh_token(user_id, email)

        with pytest.raises(ValueError, match="Invalid token type"):
            decode_access_token(refresh_token)

    def test_token_expiration(self):
        """Test that expired tokens raise error."""
        user_id = uuid4()
        email = "test@example.com"

        # Create token with immediate expiration
        payload = {
            "sub": str(user_id),
            "email": email,
            "type": "access",
            "exp": int(time.time()) - 1,  # Already expired
        }
        expired_token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        with pytest.raises(ValueError, match="Invalid token.*expired"):
            decode_access_token(expired_token)
