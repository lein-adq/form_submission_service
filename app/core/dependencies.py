"""FastAPI dependencies for authentication and database access."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db.rls import apply_rls_context
from app.core.db.session import get_db
from app.core.exceptions import AuthenticationError
from app.core.security.indentity import Identity
from app.core.security.jwt import decode_access_token

# Security scheme for OpenAPI documentation
security = HTTPBearer(
    scheme_name="Bearer",
    description="Enter your JWT access token",
    auto_error=False,  # We'll handle errors manually for better error messages
)


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(security)
    ] = None,
) -> Identity:
    """Extract and validate JWT token from Authorization header.

    Uses FastAPI's HTTPBearer for automatic OpenAPI documentation.
    """
    if not credentials:
        raise AuthenticationError("Authorization header missing")

    token = credentials.credentials
    try:
        identity = decode_access_token(token)
        return identity
    except ValueError as e:
        raise AuthenticationError(str(e))


def get_workspace_id(
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-ID")] = None,
) -> UUID | None:
    """Extract workspace ID from X-Workspace-ID header."""
    if not x_workspace_id:
        return None
    try:
        return UUID(x_workspace_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workspace ID format",
        )


def get_db_with_rls_context(
    db: Annotated[Session, Depends(get_db)],
    identity: Annotated[Identity, Depends(get_current_user)],
    workspace_id: Annotated[UUID | None, Depends(get_workspace_id)] = None,
) -> Session:
    """Get database session with RLS context applied."""
    apply_rls_context(
        db,
        user_id=str(identity.user_id),
        workspace_id=str(workspace_id) if workspace_id else None,
    )
    return db


# Dependency for optional authentication (for public endpoints)
def get_current_user_optional(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(security)
    ] = None,
) -> Identity | None:
    """Extract JWT token if present, return None otherwise.

    Useful for public endpoints that can show personalized content when authenticated.
    """
    if not credentials:
        return None
    try:
        token = credentials.credentials
        return decode_access_token(token)
    except (ValueError, AuthenticationError):
        return None
