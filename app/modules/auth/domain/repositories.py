"""Auth domain repository interfaces."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.auth.domain.entities import User


class UserRepository(ABC):
    """Repository interface for user operations."""

    @abstractmethod
    def create(self, user: User) -> User:
        """Create a new user."""
        pass

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        """Update a user."""
        pass

    @abstractmethod
    def delete(self, user_id: UUID) -> None:
        """Delete a user."""
        pass
