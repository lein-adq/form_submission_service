"""
RLS middleware for setting PostgreSQL session variables.

This middleware sets the RLS (Row-Level Security) context in the request state,
which is then used by the database dependencies to apply proper security policies.
"""

from typing import Callable

from fastapi import Request, Response

from app.core.security.jwt import decode_access_token


async def rls_middleware(request: Request, call_next: Callable) -> Response:
    """
    Set RLS context in request state for database operations.

    This middleware:
    1. Skips public/auth endpoints
    2. Extracts user_id from JWT token
    3. Extracts workspace_id from X-Workspace-ID header
    4. Stores both in request.state for database dependencies

    The actual RLS application happens in the get_db_with_rls_context dependency.
    """
    # Skip RLS for public endpoints
    public_paths = ["/health", "/docs", "/openapi.json", "/redoc", "/"]
    if any(request.url.path.startswith(path) for path in public_paths):
        return await call_next(request)

    # Skip RLS for auth endpoints (no user context yet)
    if request.url.path.startswith("/api/v1/auth"):
        return await call_next(request)

    # Extract user and workspace from headers
    authorization = request.headers.get("authorization")
    workspace_id = request.headers.get("x-workspace-id")

    # If no auth header, skip RLS (endpoint will handle auth requirement)
    if not authorization:
        return await call_next(request)

    try:
        # Decode token to get user_id
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            return await call_next(request)

        identity = decode_access_token(token)

        # Set RLS context in request state (used by get_db_with_rls_context)
        request.state.rls_user_id = str(identity.user_id)
        request.state.rls_workspace_id = workspace_id

    except (ValueError, IndexError):
        # Invalid token format, but let endpoint auth dependency handle it
        pass

    return await call_next(request)
