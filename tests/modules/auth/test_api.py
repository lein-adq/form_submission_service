"""E2E tests for auth API endpoints."""

import pytest
from fastapi.testclient import TestClient

from tests.fixtures.factories import create_user


class TestAuthRegister:
    """Test user registration endpoint."""

    def test_register_success(self, client: TestClient):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert "token" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert "access_token" in data["token"]
        assert "refresh_token" in data["token"]

    def test_register_duplicate_email(self, client: TestClient, test_user: dict):
        """Test registration with existing email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user["email"],
                "password": "password123",
            },
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email format."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": "password123",
            },
        )

        assert response.status_code == 422

    def test_register_missing_fields(self, client: TestClient):
        """Test registration with missing required fields."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com"},
        )

        assert response.status_code == 422


class TestAuthLogin:
    """Test user login endpoint."""

    def test_login_success(self, client: TestClient, test_user: dict):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "token" in data
        assert data["user"]["email"] == test_user["email"]
        assert "access_token" in data["token"]
        assert "refresh_token" in data["token"]

    def test_login_wrong_password(self, client: TestClient, test_user: dict):
        """Test login with incorrect password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent email."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_missing_fields(self, client: TestClient):
        """Test login with missing required fields."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com"},
        )

        assert response.status_code == 422


class TestAuthRefresh:
    """Test token refresh endpoint."""

    def test_refresh_token_success(self, client: TestClient, test_user: dict):
        """Test successful token refresh."""
        # First login to get refresh token
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )
        refresh_token = login_response.json()["token"]["refresh_token"]

        # Use refresh token to get new tokens
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["access_token"] != refresh_token

    def test_refresh_invalid_token(self, client: TestClient):
        """Test refresh with invalid token."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"},
        )

        assert response.status_code == 401

    def test_refresh_with_access_token(self, client: TestClient, test_user: dict):
        """Test refresh with access token (should fail)."""
        # Try to use access token as refresh token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": test_user["access_token"]},
        )

        assert response.status_code == 401


class TestAuthMe:
    """Test get current user endpoint."""

    def test_get_current_user_success(self, client: TestClient, test_user: dict):
        """Test getting current user info."""
        response = client.get(
            "/api/v1/auth/me",
            headers=test_user["token_header"],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user["id"])
        assert data["email"] == test_user["email"]

    def test_get_current_user_no_token(self, client: TestClient):
        """Test getting current user without token."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )

        assert response.status_code == 401


class TestAuthUpdateProfile:
    """Test update profile endpoint."""

    def test_update_email(self, client: TestClient, test_user: dict):
        """Test updating user email."""
        response = client.patch(
            "/api/v1/auth/me",
            headers=test_user["token_header"],
            json={"email": "newemail@example.com"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newemail@example.com"

    def test_update_password(self, client: TestClient, test_user: dict):
        """Test updating user password."""
        response = client.patch(
            "/api/v1/auth/me",
            headers=test_user["token_header"],
            json={"password": "newpassword123"},
        )

        assert response.status_code == 200

        # Verify new password works by logging in
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": "newpassword123",
            },
        )
        assert login_response.status_code == 200

    def test_update_email_to_existing(
        self, client: TestClient, test_user: dict, test_user2: dict
    ):
        """Test updating email to one that already exists."""
        response = client.patch(
            "/api/v1/auth/me",
            headers=test_user["token_header"],
            json={"email": test_user2["email"]},
        )

        assert response.status_code == 409

    def test_update_profile_no_auth(self, client: TestClient):
        """Test updating profile without authentication."""
        response = client.patch(
            "/api/v1/auth/me",
            json={"email": "newemail@example.com"},
        )

        assert response.status_code == 401


class TestAuthDeleteAccount:
    """Test delete account endpoint."""

    def test_delete_account_success(self, client: TestClient, test_user: dict):
        """Test deleting user account."""
        response = client.delete(
            "/api/v1/auth/me",
            headers=test_user["token_header"],
        )

        assert response.status_code == 204

        # Verify user can't login anymore
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )
        assert login_response.status_code == 401

    def test_delete_account_no_auth(self, client: TestClient):
        """Test deleting account without authentication."""
        response = client.delete("/api/v1/auth/me")

        assert response.status_code == 401
