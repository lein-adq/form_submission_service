"""Auth API schemas."""

from uuid import UUID

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    """Request schema for user registration."""

    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """Request schema for user login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response schema for token."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Response schema for user."""

    id: UUID
    email: str

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Response schema for login."""

    user: UserResponse
    token: TokenResponse


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh."""

    refresh_token: str


class UpdateProfileRequest(BaseModel):
    """Request schema for profile update."""

    email: EmailStr | None = None
    password: str | None = None
