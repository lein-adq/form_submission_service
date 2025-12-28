"""Authentication logging middleware."""

import time
from typing import Callable

from fastapi import Request, Response

from app.core.logging import logger
from app.core.security.jwt import decode_access_token


async def auth_logging_middleware(request: Request, call_next: Callable) -> Response:
    """Log all requests with authentication context.

    Logs:
    - User ID (if authenticated)
    - Request method and path
    - Response status code
    - Request duration
    - Client IP
    """
    start_time = time.time()

    # Extract auth info if present (don't fail on errors)
    user_id = None
    auth_header = request.headers.get("authorization")

    if auth_header:
        try:
            scheme, token = auth_header.split(" ", 1)
            if scheme.lower() == "bearer":
                identity = decode_access_token(token)
                user_id = str(identity.user_id)
                # Store in request state for downstream use
                request.state.user_id = user_id
                request.state.user_email = identity.email
        except Exception:
            # Don't fail the request if token parsing fails
            # Let the endpoint's auth dependency handle that
            pass

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Determine log level based on status code
    status_code = response.status_code
    if status_code >= 500:
        log_level = "error"
    elif status_code >= 400:
        log_level = "warning"
    else:
        log_level = "info"

    # Log request
    log_func = getattr(logger, log_level)
    log_func(
        f"{request.method} {request.url.path} -> {status_code}",
        extra={
            "user_id": user_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "duration_ms": f"{duration * 1000:.2f}",
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        },
    )

    return response
