"""Domain exceptions and FastAPI exception handlers."""

from fastapi import Request, status
from fastapi.responses import JSONResponse


class DomainException(Exception):
    """Base exception for domain errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "An error occurred"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.detail
        super().__init__(self.detail)


class NotFoundError(DomainException):
    """Resource not found."""

    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found"


class PermissionError(DomainException):
    """Permission denied."""

    status_code = status.HTTP_403_FORBIDDEN
    detail = "Permission denied"


class ValidationError(DomainException):
    """Validation error."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "Validation error"


class AuthenticationError(DomainException):
    """Authentication failed."""

    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Authentication failed"


class ConflictError(DomainException):
    """Resource conflict."""

    status_code = status.HTTP_409_CONFLICT
    detail = "Resource conflict"


async def domain_exception_handler(
    request: Request, exc: DomainException
) -> JSONResponse:
    """Handle domain exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )
