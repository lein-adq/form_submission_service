"""Auth application commands."""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class RegisterCommand:
    """Command to register a new user."""

    email: str
    password: str


@dataclass
class LoginCommand:
    """Command to login a user."""

    email: str
    password: str


@dataclass
class UpdateProfileCommand:
    """Command to update user profile."""

    user_id: UUID
    email: str | None = None
    password: str | None = None


@dataclass
class DeleteAccountCommand:
    """Command to delete a user account."""

    user_id: UUID
