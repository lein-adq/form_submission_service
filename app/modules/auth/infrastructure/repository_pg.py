"""PostgreSQL implementation of user repository."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.db.models import User as UserModel
from app.modules.auth.domain.entities import User
from app.modules.auth.domain.repositories import UserRepository


class PostgreSQLUserRepository(UserRepository):
    """PostgreSQL implementation of UserRepository."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user: User) -> User:
        """Create a new user."""
        db_user = UserModel(
            email=user.email,
            password_hash=user.password_hash,
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return User(
            id=db_user.id,
            email=db_user.email,
            password_hash=db_user.password_hash,
        )

    def get_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not db_user:
            return None
        return User(
            id=db_user.id,
            email=db_user.email,
            password_hash=db_user.password_hash,
        )

    def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        db_user = (
            self.db.query(UserModel)
            .filter(UserModel.email == email.lower().strip())
            .first()
        )
        if not db_user:
            return None
        return User(
            id=db_user.id,
            email=db_user.email,
            password_hash=db_user.password_hash,
        )

    def update(self, user: User) -> User:
        """Update a user."""
        db_user = self.db.query(UserModel).filter(UserModel.id == user.id).first()
        if not db_user:
            raise ValueError("User not found")
        db_user.email = user.email
        db_user.password_hash = user.password_hash
        self.db.commit()
        self.db.refresh(db_user)
        return User(
            id=db_user.id,
            email=db_user.email,
            password_hash=db_user.password_hash,
        )

    def delete(self, user_id: UUID) -> None:
        """Delete a user."""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if db_user:
            self.db.delete(db_user)
            self.db.commit()
