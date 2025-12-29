"""Shared pytest fixtures for all tests."""

import os
from typing import Annotated, Generator
from uuid import UUID

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.db.rls import apply_rls_context
from app.core.db.session import get_db, get_service_db
from app.core.dependencies import (
    get_current_user,
    get_db_with_rls_context,
    get_workspace_id,
)
from app.core.security.indentity import Identity
from app.core.security.jwt import create_access_token
from app.main import app

# Test database URL - use environment variable or default to test database
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/formcore_test"
)


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine for the entire test session."""
    engine = create_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def setup_test_database(test_engine):
    """Run migrations on test database before all tests."""
    from alembic import command
    from alembic.config import Config

    # Run migrations
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)

    # Upgrade to head (apply all migrations)
    command.upgrade(alembic_cfg, "head")

    yield

    # Optional: Downgrade after all tests (uncomment if needed)
    # command.downgrade(alembic_cfg, "base")


@pytest.fixture(scope="function")
def db_session(test_engine, setup_test_database) -> Generator[Session, None, None]:
    """Create a new database session for each test with transaction rollback."""
    connection = test_engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()

    # Set bypass for test fixtures to allow creating test data
    from sqlalchemy import text
    session.execute(text("SET LOCAL app.bypass_rls = 'on'"))

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a FastAPI test client with overridden database dependency."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_service_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_db_with_rls_context(
        identity: Annotated[Identity, Depends(get_current_user)],
        workspace_id: Annotated[UUID | None, Depends(get_workspace_id)] = None,
    ):
        """
        Override get_db_with_rls_context to use test session with RLS context.

        This ensures the same session is used for both service factories and endpoints,
        with RLS context applied based on the identity and workspace_id from the request.

        The signature matches the original dependency so FastAPI can properly resolve
        the nested dependencies (get_current_user and get_workspace_id).
        """
        # Apply RLS context to the test session using the identity from the request
        # Make sure bypass is disabled for API calls
        from sqlalchemy import text
        db_session.execute(text("SET LOCAL app.bypass_rls = 'off'"))
        apply_rls_context(
            db_session,
            user_id=str(identity.user_id),
            workspace_id=str(workspace_id) if workspace_id else None,
        )
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_service_db] = override_get_service_db
    app.dependency_overrides[get_db_with_rls_context] = override_get_db_with_rls_context

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session: Session) -> dict:
    """Create a test user and return user data with token."""
    from app.core.security.hashing import hash_password
    from app.core.db.models import User as UserModel

    email = "test@example.com"
    password = "testpassword123"
    password_hash = hash_password(password)

    user = UserModel(
        email=email,
        password_hash=password_hash,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    access_token = create_access_token(user.id, user.email)

    return {
        "id": user.id,
        "email": email,
        "password": password,
        "access_token": access_token,
        "token_header": {"Authorization": f"Bearer {access_token}"},
    }


@pytest.fixture(scope="function")
def test_user2(db_session: Session) -> dict:
    """Create a second test user for multi-user tests."""
    from app.core.security.hashing import hash_password
    from app.core.db.models import User as UserModel

    email = "test2@example.com"
    password = "testpassword456"
    password_hash = hash_password(password)

    user = UserModel(
        email=email,
        password_hash=password_hash,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    access_token = create_access_token(user.id, user.email)

    return {
        "id": user.id,
        "email": email,
        "password": password,
        "access_token": access_token,
        "token_header": {"Authorization": f"Bearer {access_token}"},
    }


@pytest.fixture(scope="function")
def test_workspace(db_session: Session, test_user: dict) -> dict:
    """Create a test workspace owned by test_user."""
    from app.core.db.models import Workspace as WorkspaceModel
    from app.core.db.models import WorkspaceMember as WorkspaceMemberModel

    workspace = WorkspaceModel(
        name="Test Workspace",
    )
    db_session.add(workspace)
    db_session.commit()
    db_session.refresh(workspace)

    # Add creator as owner
    membership = WorkspaceMemberModel(
        workspace_id=workspace.id,
        user_id=test_user["id"],
        role="owner",
    )
    db_session.add(membership)
    db_session.commit()

    return {
        "id": workspace.id,
        "name": workspace.name,
        "owner_id": test_user["id"],
    }


@pytest.fixture(scope="function")
def test_workspace2(db_session: Session, test_user2: dict) -> dict:
    """Create a second test workspace owned by test_user2."""
    from app.core.db.models import Workspace as WorkspaceModel
    from app.core.db.models import WorkspaceMember as WorkspaceMemberModel

    workspace = WorkspaceModel(
        name="Test Workspace 2",
    )
    db_session.add(workspace)
    db_session.commit()
    db_session.refresh(workspace)

    # Add creator as owner
    membership = WorkspaceMemberModel(
        workspace_id=workspace.id,
        user_id=test_user2["id"],
        role="owner",
    )
    db_session.add(membership)
    db_session.commit()

    return {
        "id": workspace.id,
        "name": workspace.name,
        "owner_id": test_user2["id"],
    }


@pytest.fixture(scope="function")
def auth_client(client: TestClient, test_user: dict) -> TestClient:
    """Return a client with pre-configured authentication headers."""
    client.headers.update(test_user["token_header"])
    return client


@pytest.fixture(scope="function")
def mock_current_user(test_user: dict):
    """Mock the get_current_user dependency for unit tests."""

    def _mock_user():
        return Identity(
            user_id=test_user["id"],
            email=test_user["email"],
        )

    return _mock_user


@pytest.fixture(scope="function")
def rls_context(db_session: Session, test_user: dict, test_workspace: dict):
    """Apply RLS context to database session for testing RLS policies."""
    from app.core.db.rls import apply_rls_context

    apply_rls_context(
        db_session,
        user_id=str(test_user["id"]),
        workspace_id=str(test_workspace["id"]),
    )

    return {
        "user_id": test_user["id"],
        "workspace_id": test_workspace["id"],
    }
