# Testing

This guide covers testing practices, structure, and how to run tests for the FormCore application.

## Overview

FormCore uses a comprehensive testing approach with three test types:

- **Unit Tests**: Test business logic in isolation with mocked dependencies
- **E2E Tests**: Test complete HTTP request/response cycles with real database
- **Integration Tests**: Test cross-module interactions and system-wide features like RLS

## Test Organization

Tests mirror the application structure:

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── core/                    # Tests for core utilities
├── modules/                 # Tests mirroring app/modules/
│   ├── auth/
│   │   ├── test_api.py      # E2E: API endpoint tests
│   │   ├── test_services.py # Unit: Business logic tests
│   │   └── test_repositories.py # Unit: Data layer tests
│   └── [other modules follow same pattern]
├── integration/             # Cross-module integration tests
└── fixtures/                # Test data factories and utilities
```

Each module follows a consistent pattern:
- `test_api.py` - E2E tests for API endpoints
- `test_services.py` - Unit tests for application services
- `test_repositories.py` - Unit tests for repositories
- `test_policies.py` - Unit tests for domain policies (when applicable)

## Running Tests

### Using Docker (Recommended)

All tests run in Docker containers to ensure consistency and isolation:

```bash
# Start test database
docker compose -f compose.test.yml up -d formcore-test-db

# Run all tests
docker compose -f compose.test.yml run --rm formcore-test pytest

# Run with verbose output
docker compose -f compose.test.yml run --rm formcore-test pytest -v

# Run with coverage report
docker compose -f compose.test.yml run --rm formcore-test pytest --cov=app --cov-report=html --cov-report=term

# View coverage (open htmlcov/index.html in browser after running)
```

### Run Specific Test Types

```bash
# Unit tests only
docker compose -f compose.test.yml run --rm formcore-test pytest tests/modules/ -k "test_services or test_repositories" tests/core/

# E2E/API tests only
docker compose -f compose.test.yml run --rm formcore-test pytest tests/modules/ -k "test_api"

# Integration tests only
docker compose -f compose.test.yml run --rm formcore-test pytest tests/integration/

# Specific module
docker compose -f compose.test.yml run --rm formcore-test pytest tests/modules/auth/

# Specific test file
docker compose -f compose.test.yml run --rm formcore-test pytest tests/modules/auth/test_api.py

# Specific test
docker compose -f compose.test.yml run --rm formcore-test pytest tests/modules/auth/test_api.py::TestAuthRegister::test_register_success
```

## Writing Tests

### Test Structure

Follow the AAA pattern: **Arrange, Act, Assert**

```python
def test_create_form(client, test_user, test_workspace):
    # Arrange
    payload = {"name": "Test Form"}
    
    # Act
    response = client.post(
        f"/api/v1/workspaces/{test_workspace['id']}/forms",
        headers=test_user["token_header"],
        json=payload,
    )
    
    # Assert
    assert response.status_code == 201
    assert response.json()["name"] == "Test Form"
```

### Using Fixtures

Common fixtures available in `conftest.py`:

```python
def test_example(
    client,          # FastAPI TestClient
    db_session,      # Database session with rollback
    test_user,       # Pre-created user with token
    test_workspace,  # Pre-created workspace
):
    # Test implementation
    pass
```

See `tests/conftest.py` for complete fixture list and documentation.

### Using Factories

Create test data using factory functions:

```python
from tests.fixtures.factories import create_user, create_form

def test_example(db_session):
    user = create_user(db_session, email="test@example.com")
    form = create_form(
        db_session,
        workspace_id=workspace.id,
        name="My Form",
    )
    # Test implementation
```

### Unit Test Example

Unit tests should mock external dependencies:

```python
from unittest.mock import Mock
from app.modules.auth.application.services import AuthService

def test_login_success():
    # Mock repository
    mock_repo = Mock()
    mock_repo.get_by_email.return_value = user
    
    # Test service
    service = AuthService(mock_repo)
    result = service.login(command)
    
    # Verify
    assert result.email == "test@example.com"
    mock_repo.get_by_email.assert_called_once()
```

### E2E Test Example

E2E tests use real database and full HTTP stack:

```python
def test_register_endpoint(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "secure_password",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data["token"]
```

### Integration Test Example

Integration tests verify cross-module interactions:

```python
def test_workspace_isolation(
    client,
    test_user,
    test_workspace,
    test_workspace2,
    db_session,
):
    """Verify user cannot access other workspace's data."""
    form = create_form(db_session, workspace_id=test_workspace2["id"])
    
    response = client.get(
        f"/api/v1/workspaces/{test_workspace2['id']}/forms/{form.id}",
        headers={
            **test_user["token_header"],
            "X-Workspace-ID": str(test_workspace2["id"]),
        },
    )
    
    # Should fail - user not member of workspace2
    assert response.status_code in [403, 404]
```

## Test Configuration

### Environment Variables

Create `.env.test` for test-specific configuration:

```env
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5433/formcore_test
JWT_SECRET_KEY=test-secret-key
ENVIRONMENT=test
DEBUG=false
```

### Pytest Configuration

Configuration in `pytest.ini` includes:

- Test discovery patterns
- Markers for categorizing tests
- Coverage settings
- Output formatting

### Coverage Configuration

Coverage settings in `pytest.ini` exclude:

- Migration files
- Test files themselves
- Generated code
- Development utilities

## Test Database Management

### Using Docker Compose

The test database runs in a Docker container:

```bash
# Start test database
docker compose -f compose.test.yml up -d formcore-test-db

# Check database status
docker compose -f compose.test.yml ps

# View database logs
docker compose -f compose.test.yml logs formcore-test-db

# Stop test database
docker compose -f compose.test.yml down

# Reset test database (clean slate)
docker compose -f compose.test.yml down -v
docker compose -f compose.test.yml up -d formcore-test-db
```

### Run Migrations

Migrations are automatically run when the test container starts, but you can run them manually:

```bash
docker compose -f compose.test.yml run --rm formcore-test alembic upgrade head
```

## Continuous Integration

For CI/CD pipelines:

```bash
# Start services
docker compose -f compose.test.yml up -d formcore-test-db

# Run tests with coverage
docker compose -f compose.test.yml run --rm formcore-test pytest --cov=app --cov-report=xml --cov-report=term

# Cleanup
docker compose -f compose.test.yml down -v
```

## Best Practices

1. **Keep tests independent**: Each test should work in isolation
2. **Use descriptive names**: Test names should explain what they verify
3. **Test edge cases**: Include error conditions and boundary cases
4. **Mock external dependencies**: Unit tests should not depend on external services
5. **Use fixtures wisely**: Share setup code but maintain test clarity
6. **Clean up resources**: Use fixtures with proper teardown
7. **Test behavior, not implementation**: Focus on what the code does, not how
8. **Keep tests fast**: Use unit tests for business logic, E2E for critical paths

## Troubleshooting

### Database Connection Issues

```bash
# Check if test database is running
docker compose -f compose.test.yml ps

# Check database logs
docker compose -f compose.test.yml logs formcore-test-db

# Restart database
docker compose -f compose.test.yml restart formcore-test-db
```

### Migration Issues

```bash
# Check current migration version
alembic current

# Reset and re-run migrations
docker compose -f compose.test.yml down -v
docker compose -f compose.test.yml up -d
alembic upgrade head
```

### Import Errors

```bash
# Reinstall dependencies
uv sync --group dev

# Check Python version (needs 3.12+)
python --version
```

### Slow Tests

```bash
# Run only fast tests (skip integration tests)
pytest -m "not slow"

# Use parallel execution (requires pytest-xdist)
pytest -n auto
```

## Coverage Goals

- **Overall**: 80%+ code coverage
- **Critical paths**: 100% coverage for authentication and authorization
- **Business logic**: 90%+ coverage for service layer
- **API endpoints**: 80%+ coverage for all endpoints

Check current coverage:

```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## Additional Resources

- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- See `tests/README.md` for detailed fixture documentation

