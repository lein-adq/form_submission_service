"""Auth API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.middleware.rate_limit import limiter
from app.core.security.indentity import Identity
from app.core.exceptions import NotFoundError
from app.modules.auth.api.schemas import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)
from app.modules.auth.application.commands import (
    DeleteAccountCommand,
    LoginCommand,
    RegisterCommand,
    UpdateProfileCommand,
)
from app.modules.auth.application.services import AuthService
from app.modules.auth.infrastructure.repository_pg import PostgreSQLUserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: Annotated[Session, Depends(get_db)]) -> AuthService:
    """Dependency for auth service."""
    repository = PostgreSQLUserRepository(db)
    return AuthService(repository)


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=LoginResponse
)
@limiter.limit("5/minute")  # Rate limit: 5 registrations per minute per IP
def register(
    request: Request,
    data: RegisterRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    """Register a new user.

    Returns both access and refresh tokens for immediate login.
    """
    command = RegisterCommand(email=data.email, password=data.password)
    try:
        user, access_token, refresh_token = service.register(command)
        return LoginResponse(
            user=UserResponse(id=user.id, email=user.email),
            token=TokenResponse(access_token=access_token, refresh_token=refresh_token),
        )
    except ConflictError as e:
        raise ConflictError(str(e)) from e


@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")  # Rate limit: 10 login attempts per minute per IP
def login(
    request: Request,
    data: LoginRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    """Login a user.

    Returns both access and refresh tokens.
    Access tokens expire in 30 minutes, refresh tokens in 7 days.
    """
    command = LoginCommand(email=data.email, password=data.password)
    try:
        user, access_token, refresh_token = service.login(command)
        return LoginResponse(
            user=UserResponse(id=user.id, email=user.email),
            token=TokenResponse(access_token=access_token, refresh_token=refresh_token),
        )
    except AuthenticationError as e:
        raise AuthenticationError(str(e)) from e


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")  # Rate limit: 20 refresh requests per minute per IP
def refresh_token(
    request: Request,
    data: RefreshTokenRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Refresh access token using a valid refresh token.

    Returns new access and refresh tokens. Old tokens are invalidated.
    """
    try:
        access_token, refresh_token = service.refresh_access_token(data.refresh_token)
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
    except AuthenticationError as e:
        raise AuthenticationError(str(e)) from e


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    identity: Annotated[Identity, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """Get current user information.

    Requires valid access token in Authorization header.
    """
    user = service.user_repository.get_by_id(identity.user_id)
    if not user:
        raise AuthenticationError("User not found")
    return UserResponse(id=user.id, email=user.email)


@router.patch("/me", response_model=UserResponse)
def update_profile(
    identity: Annotated[Identity, Depends(get_current_user)],
    data: UpdateProfileRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """Update current user's profile.

    Allows updating email and/or password.
    Requires valid access token in Authorization header.
    """
    command = UpdateProfileCommand(
        user_id=identity.user_id,
        email=data.email,
        password=data.password,
    )
    try:
        user = service.update_profile(command)
        return UserResponse(id=user.id, email=user.email)
    except (NotFoundError, ConflictError) as e:
        raise e


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    identity: Annotated[Identity, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> None:
    """Delete current user's account.

    This action is irreversible.
    Requires valid access token in Authorization header.
    """
    command = DeleteAccountCommand(user_id=identity.user_id)
    try:
        service.delete_account(command)
    except NotFoundError as e:
        raise e
