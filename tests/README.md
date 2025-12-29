# Tests

This directory contains the test suite for FormCore.

## Quick Start

```bash
# 1. Start test database
docker compose -f compose.test.yml up -d formcore-test-db

# 2. Run tests
docker compose -f compose.test.yml run --rm formcore-test pytest
```

## Structure

Tests mirror the application structure:

- `core/` - Core utility tests (JWT, hashing, etc.)
- `modules/auth/` - Auth module tests
- `modules/workspaces/` - Workspace module tests
- `modules/forms/` - Form module tests
- `modules/submissions/` - Submission module tests
- `integration/` - Cross-module integration tests
- `fixtures/` - Test data factories and utilities
- `conftest.py` - Shared fixtures and configuration

Each module contains:
- `test_api.py` - E2E tests for API endpoints
- `test_services.py` - Unit tests for business logic
- `test_repositories.py` - Unit tests for data layer

## Available Fixtures

### Database
- `db_session` - Database session with automatic rollback
- `test_engine` - Test database engine
- `setup_test_database` - Runs migrations on test database

### Test Client
- `client` - FastAPI TestClient with dependency overrides
- `auth_client` - Client with pre-configured authentication

### Test Data
- `test_user` - Pre-created user with access token
- `test_user2` - Second test user for multi-user scenarios
- `test_workspace` - Workspace owned by test_user
- `test_workspace2` - Workspace owned by test_user2
- `rls_context` - Database session with RLS context applied

### Helpers
- `mock_current_user` - Mock user identity for unit tests

## Factory Functions

Create test data using factories from `fixtures/factories.py`:

```python
from tests.fixtures.factories import (
    create_user,
    create_workspace,
    create_form,
    create_submission,
)

def test_example(db_session):
    user = create_user(db_session)
    workspace = create_workspace(db_session, owner_id=user.id)
    form = create_form(db_session, workspace_id=workspace.id)
```

## Running Specific Tests

```bash
# All tests
docker compose -f compose.test.yml run --rm formcore-test pytest

# Specific module
docker compose -f compose.test.yml run --rm formcore-test pytest tests/modules/auth/

# Unit tests only
docker compose -f compose.test.yml run --rm formcore-test pytest tests/modules/ -k "test_services or test_repositories"

# E2E tests only
docker compose -f compose.test.yml run --rm formcore-test pytest tests/modules/ -k "test_api"

# With coverage
docker compose -f compose.test.yml run --rm formcore-test pytest --cov=app --cov-report=html
```

## Documentation

For comprehensive testing documentation, see:
- [docs/testing.md](../docs/testing.md) - Complete testing guide
- [docs/development.md](../docs/development.md) - Development setup

## Test Types

**Unit Tests** - Fast, isolated tests with mocked dependencies
- `test_services.py` - Business logic
- `test_repositories.py` - Data layer
- `test_policies.py` - Domain policies

**E2E Tests** - Full HTTP request/response cycle
- `test_api.py` - API endpoints with real database

**Integration Tests** - Cross-module interactions
- `integration/test_rls.py` - Multi-tenant isolation
