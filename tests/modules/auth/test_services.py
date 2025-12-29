"""Unit tests for auth services."""

from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.core.security.hashing import hash_password, verify_password
from app.modules.auth.application.commands import (
    DeleteAccountCommand,
    LoginCommand,
    RegisterCommand,
    UpdateProfileCommand,
)
from app.modules.auth.application.services import AuthService
from app.modules.auth.domain.entities import User


class TestAuthService:
    """Test AuthService business logic."""

    def test_register_success(self):
        """Test successful user registration."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_by_email.return_value = None  # User doesn't exist

        # Mock created user
        created_user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash="hashed_password",
        )
        mock_repo.create.return_value = created_user

        service = AuthService(mock_repo)
        command = RegisterCommand(email="test@example.com", password="password123")

        user, access_token, refresh_token = service.register(command)

        assert user.id == created_user.id
        assert user.email == "test@example.com"
        assert access_token is not None
        assert refresh_token is not None
        mock_repo.get_by_email.assert_called_once_with("test@example.com")
        mock_repo.create.assert_called_once()

    def test_register_duplicate_email(self):
        """Test registration with existing email."""
        # Mock repository
        mock_repo = Mock()
        existing_user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash="hashed_password",
        )
        mock_repo.get_by_email.return_value = existing_user

        service = AuthService(mock_repo)
        command = RegisterCommand(email="test@example.com", password="password123")

        with pytest.raises(ConflictError, match="User with this email already exists"):
            service.register(command)

    def test_login_success(self):
        """Test successful login."""
        # Mock repository
        mock_repo = Mock()
        password = "password123"
        password_hash = hash_password(password)

        user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash=password_hash,
        )
        mock_repo.get_by_email.return_value = user

        service = AuthService(mock_repo)
        command = LoginCommand(email="test@example.com", password=password)

        result_user, access_token, refresh_token = service.login(command)

        assert result_user.id == user.id
        assert result_user.email == user.email
        assert access_token is not None
        assert refresh_token is not None

    def test_login_user_not_found(self):
        """Test login with non-existent user."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_by_email.return_value = None

        service = AuthService(mock_repo)
        command = LoginCommand(email="test@example.com", password="password123")

        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            service.login(command)

    def test_login_wrong_password(self):
        """Test login with incorrect password."""
        # Mock repository
        mock_repo = Mock()
        password = "correct_password"
        password_hash = hash_password(password)

        user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash=password_hash,
        )
        mock_repo.get_by_email.return_value = user

        service = AuthService(mock_repo)
        command = LoginCommand(email="test@example.com", password="wrong_password")

        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            service.login(command)

    def test_refresh_access_token_success(self):
        """Test refreshing access token."""
        from app.core.security.jwt import create_refresh_token

        # Mock repository
        mock_repo = Mock()
        user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash="hashed_password",
        )
        mock_repo.get_by_id.return_value = user

        service = AuthService(mock_repo)
        refresh_token = create_refresh_token(user.id, user.email)

        new_access_token, new_refresh_token = service.refresh_access_token(
            refresh_token
        )

        assert new_access_token is not None
        assert new_refresh_token is not None
        assert new_access_token != refresh_token

    def test_refresh_access_token_invalid_token(self):
        """Test refreshing with invalid token."""
        mock_repo = Mock()
        service = AuthService(mock_repo)

        with pytest.raises(AuthenticationError):
            service.refresh_access_token("invalid_token")

    def test_refresh_access_token_user_not_found(self):
        """Test refreshing when user no longer exists."""
        from app.core.security.jwt import create_refresh_token

        # Mock repository
        mock_repo = Mock()
        mock_repo.get_by_id.return_value = None

        service = AuthService(mock_repo)
        user_id = uuid4()
        refresh_token = create_refresh_token(user_id, "test@example.com")

        with pytest.raises(AuthenticationError, match="User not found"):
            service.refresh_access_token(refresh_token)

    def test_update_profile_email(self):
        """Test updating user email."""
        mock_repo = Mock()
        user = User(
            id=uuid4(),
            email="old@example.com",
            password_hash="hashed_password",
        )
        mock_repo.get_by_id.return_value = user
        mock_repo.get_by_email.return_value = None  # New email not taken
        mock_repo.update.return_value = user

        service = AuthService(mock_repo)
        command = UpdateProfileCommand(
            user_id=user.id,
            email="new@example.com",
        )

        updated_user = service.update_profile(command)

        mock_repo.update.assert_called_once()
        assert updated_user.email == "new@example.com"

    def test_update_profile_email_conflict(self):
        """Test updating to an already taken email."""
        mock_repo = Mock()
        user = User(
            id=uuid4(),
            email="old@example.com",
            password_hash="hashed_password",
        )
        existing_user = User(
            id=uuid4(),
            email="taken@example.com",
            password_hash="hashed_password",
        )
        mock_repo.get_by_id.return_value = user
        mock_repo.get_by_email.return_value = existing_user

        service = AuthService(mock_repo)
        command = UpdateProfileCommand(
            user_id=user.id,
            email="taken@example.com",
        )

        with pytest.raises(ConflictError, match="Email already in use"):
            service.update_profile(command)

    def test_update_profile_password(self):
        """Test updating user password."""
        mock_repo = Mock()
        user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash=hash_password("old_password"),
        )
        mock_repo.get_by_id.return_value = user
        mock_repo.update.return_value = user

        service = AuthService(mock_repo)
        command = UpdateProfileCommand(
            user_id=user.id,
            password="new_password",
        )

        updated_user = service.update_profile(command)

        mock_repo.update.assert_called_once()
        # Verify new password works
        assert verify_password("new_password", updated_user.password_hash)

    def test_update_profile_user_not_found(self):
        """Test updating profile for non-existent user."""
        mock_repo = Mock()
        mock_repo.get_by_id.return_value = None

        service = AuthService(mock_repo)
        command = UpdateProfileCommand(
            user_id=uuid4(),
            email="new@example.com",
        )

        with pytest.raises(NotFoundError, match="User not found"):
            service.update_profile(command)

    def test_delete_account_success(self):
        """Test deleting user account."""
        mock_repo = Mock()
        user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash="hashed_password",
        )
        mock_repo.get_by_id.return_value = user

        service = AuthService(mock_repo)
        command = DeleteAccountCommand(user_id=user.id)

        service.delete_account(command)

        mock_repo.delete.assert_called_once_with(user.id)

    def test_delete_account_user_not_found(self):
        """Test deleting non-existent user."""
        mock_repo = Mock()
        mock_repo.get_by_id.return_value = None

        service = AuthService(mock_repo)
        command = DeleteAccountCommand(user_id=uuid4())

        with pytest.raises(NotFoundError, match="User not found"):
            service.delete_account(command)
