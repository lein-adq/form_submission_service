"""Auth application services."""

from uuid import UUID

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security.hashing import hash_password, verify_password
from app.core.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.core.exceptions import NotFoundError
from app.modules.auth.application.commands import (
    DeleteAccountCommand,
    LoginCommand,
    RegisterCommand,
    UpdateProfileCommand,
)
from app.modules.auth.domain.entities import User
from app.modules.auth.domain.repositories import UserRepository


class AuthService:
    """Service for authentication operations."""

    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def register(self, command: RegisterCommand) -> tuple[User, str, str]:
        """Register a new user and return user with access and refresh tokens."""
        # Check if user already exists
        existing_user = self.user_repository.get_by_email(command.email)
        if existing_user:
            raise ConflictError("User with this email already exists")

        # Create new user
        password_hash = hash_password(command.password)
        user = User(
            id=UUID(int=0),  # Will be set by repository
            email=command.email.lower().strip(),
            password_hash=password_hash,
        )
        created_user = self.user_repository.create(user)

        # Generate tokens
        access_token = create_access_token(created_user.id, created_user.email)
        refresh_token = create_refresh_token(created_user.id, created_user.email)

        return created_user, access_token, refresh_token

    def login(self, command: LoginCommand) -> tuple[User, str, str]:
        """Login a user and return user with access and refresh tokens."""
        user = self.user_repository.get_by_email(command.email.lower().strip())
        if not user:
            raise AuthenticationError("Invalid email or password")

        if not verify_password(command.password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        # Generate tokens
        access_token = create_access_token(user.id, user.email)
        refresh_token = create_refresh_token(user.id, user.email)

        return user, access_token, refresh_token

    def refresh_access_token(self, refresh_token: str) -> tuple[str, str]:
        """Refresh access token using a valid refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Tuple of (new_access_token, new_refresh_token)

        Raises:
            AuthenticationError: If refresh token is invalid or user not found
        """
        try:
            identity = decode_refresh_token(refresh_token)
            user = self.user_repository.get_by_id(identity.user_id)
            if not user:
                raise AuthenticationError("User not found")

            # Generate new tokens
            new_access_token = create_access_token(user.id, user.email)
            new_refresh_token = create_refresh_token(user.id, user.email)

            return new_access_token, new_refresh_token
        except ValueError as e:
            raise AuthenticationError(str(e)) from e

    def verify_token(self, token: str) -> User:
        """Verify a JWT token and return the user."""
        from app.core.security.jwt import decode_access_token

        try:
            identity = decode_access_token(token)
            user = self.user_repository.get_by_id(identity.user_id)
            if not user:
                raise AuthenticationError("User not found")
            return user
        except ValueError as e:
            raise AuthenticationError(str(e)) from e

    def update_profile(self, command: UpdateProfileCommand) -> User:
        """Update user profile (email and/or password)."""
        user = self.user_repository.get_by_id(command.user_id)
        if not user:
            raise NotFoundError("User not found")

        # Check if new email is already taken
        if command.email and command.email.lower().strip() != user.email:
            existing = self.user_repository.get_by_email(command.email)
            if existing:
                raise ConflictError("Email already in use")
            user.email = command.email.lower().strip()

        # Update password if provided
        if command.password:
            user.password_hash = hash_password(command.password)

        return self.user_repository.update(user)

    def delete_account(self, command: DeleteAccountCommand) -> None:
        """Delete a user account."""
        user = self.user_repository.get_by_id(command.user_id)
        if not user:
            raise NotFoundError("User not found")

        self.user_repository.delete(command.user_id)
