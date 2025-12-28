"""JWT token utilities."""

from datetime import datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt

from app.core.config.settings import settings
from app.core.security.indentity import Identity


def create_access_token(user_id: UUID, email: str) -> str:
    """Create a JWT access token.

    Args:
        user_id: User's unique identifier
        email: User's email address

    Returns:
        Encoded JWT access token (short-lived)
    """
    expire = datetime.utcnow() + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    to_encode = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "type": "access",
    }
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def create_refresh_token(user_id: UUID, email: str) -> str:
    """Create a JWT refresh token.

    Args:
        user_id: User's unique identifier
        email: User's email address

    Returns:
        Encoded JWT refresh token (long-lived)
    """
    expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
    to_encode = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "type": "refresh",
    }
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> Identity:
    """Decode and validate a JWT access token.

    Args:
        token: JWT token string

    Returns:
        Identity object with user information

    Raises:
        ValueError: If token is invalid, expired, or not an access token
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        token_type: str = payload.get("type", "access")

        if user_id is None or email is None:
            raise ValueError("Invalid token payload")

        if token_type != "access":
            raise ValueError("Invalid token type")

        return Identity(user_id=UUID(user_id), email=email)
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e


def decode_refresh_token(token: str) -> Identity:
    """Decode and validate a JWT refresh token.

    Args:
        token: JWT refresh token string

    Returns:
        Identity object with user information

    Raises:
        ValueError: If token is invalid, expired, or not a refresh token
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        token_type: str = payload.get("type", "access")

        if user_id is None or email is None:
            raise ValueError("Invalid token payload")

        if token_type != "refresh":
            raise ValueError("Invalid token type")

        return Identity(user_id=UUID(user_id), email=email)
    except JWTError as e:
        raise ValueError(f"Invalid refresh token: {e}") from e
