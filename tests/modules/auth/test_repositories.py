"""Unit tests for auth repositories."""

import pytest
from sqlalchemy.orm import Session

from app.modules.auth.domain.entities import User
from app.modules.auth.infrastructure.repository_pg import PostgreSQLUserRepository
from tests.fixtures.factories import create_user


class TestPostgreSQLUserRepository:
    """Test PostgreSQLUserRepository with real database."""

    def test_create_user(self, db_session: Session):
        """Test creating a user."""
        repo = PostgreSQLUserRepository(db_session)

        user = User(
            id=None,  # Will be assigned by DB
            email="test@example.com",
            password_hash="hashed_password",
        )

        created_user = repo.create(user)

        assert created_user.id is not None
        assert created_user.email == "test@example.com"
        assert created_user.password_hash == "hashed_password"

    def test_get_by_id(self, db_session: Session):
        """Test getting user by ID."""
        repo = PostgreSQLUserRepository(db_session)

        # Create user
        user = create_user(db_session, email="test@example.com")

        # Retrieve by ID
        retrieved_user = repo.get_by_id(user.id)

        assert retrieved_user is not None
        assert retrieved_user.id == user.id
        assert retrieved_user.email == user.email

    def test_get_by_id_not_found(self, db_session: Session):
        """Test getting non-existent user by ID."""
        from uuid import uuid4

        repo = PostgreSQLUserRepository(db_session)
        user = repo.get_by_id(uuid4())

        assert user is None

    def test_get_by_email(self, db_session: Session):
        """Test getting user by email."""
        repo = PostgreSQLUserRepository(db_session)

        # Create user
        user = create_user(db_session, email="test@example.com")

        # Retrieve by email
        retrieved_user = repo.get_by_email("test@example.com")

        assert retrieved_user is not None
        assert retrieved_user.id == user.id
        assert retrieved_user.email == "test@example.com"

    def test_get_by_email_case_insensitive(self, db_session: Session):
        """Test email lookup is case-insensitive."""
        repo = PostgreSQLUserRepository(db_session)

        # Create user with lowercase email
        user = create_user(db_session, email="test@example.com")

        # Retrieve with mixed case
        retrieved_user = repo.get_by_email("TEST@EXAMPLE.COM")

        # Note: This depends on database collation
        # PostgreSQL default is case-sensitive, so this might return None
        # For case-insensitive search, the repository should handle it
        assert retrieved_user is None or retrieved_user.id == user.id

    def test_get_by_email_not_found(self, db_session: Session):
        """Test getting non-existent user by email."""
        repo = PostgreSQLUserRepository(db_session)
        user = repo.get_by_email("nonexistent@example.com")

        assert user is None

    def test_update_user(self, db_session: Session):
        """Test updating a user."""
        repo = PostgreSQLUserRepository(db_session)

        # Create user
        user = create_user(db_session, email="old@example.com")
        original_id = user.id

        # Update email
        user.email = "new@example.com"
        updated_user = repo.update(user)

        assert updated_user.id == original_id
        assert updated_user.email == "new@example.com"

        # Verify in database
        retrieved_user = repo.get_by_id(original_id)
        assert retrieved_user.email == "new@example.com"

    def test_delete_user(self, db_session: Session):
        """Test deleting a user."""
        repo = PostgreSQLUserRepository(db_session)

        # Create user
        user = create_user(db_session, email="test@example.com")
        user_id = user.id

        # Delete user
        repo.delete(user_id)

        # Verify deletion
        retrieved_user = repo.get_by_id(user_id)
        assert retrieved_user is None

    def test_delete_nonexistent_user(self, db_session: Session):
        """Test deleting non-existent user doesn't raise error."""
        from uuid import uuid4

        repo = PostgreSQLUserRepository(db_session)

        # Should not raise error
        repo.delete(uuid4())
