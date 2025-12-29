# Development Guide

## Local Development Without Docker

### Prerequisites

- Python 3.12+
- PostgreSQL 16
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip

### Setup

1. **Install dependencies**

   ```bash
   uv sync
   # or
   pip install -e .
   ```

2. **Set up PostgreSQL database**

   ```bash
   createdb formcore
   # Or use your preferred method to create the database
   ```

3. **Configure environment variables**
   Create a `.env` file:

   ```env
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/formcore
   JWT_SECRET_KEY=your-dev-secret-key
   CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
   ENVIRONMENT=development
   DEBUG=true
   ```

4. **Run migrations**

   ```bash
   alembic upgrade head
   ```

5. **Start the development server**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at http://localhost:8000

## Project Structure

See [Architecture](architecture.md) for detailed structure explanation.

## Running Tests

### Quick Start

```bash
# Start test database
docker compose -f compose.test.yml up -d formcore-test-db

# Run all tests
docker compose -f compose.test.yml run --rm formcore-test pytest

# Run with coverage
docker compose -f compose.test.yml run --rm formcore-test pytest --cov=app --cov-report=html --cov-report=term
```

### Test Database Setup

The test suite uses a separate PostgreSQL database running in Docker:

- **Database**: `formcore_test`
- **Container**: `formcore-test-db`
- **Configuration**: `compose.test.yml`

**Start test database:**
```bash
docker compose -f compose.test.yml up -d formcore-test-db
```

**Stop test database:**
```bash
docker compose -f compose.test.yml down
```

**Reset test database (clean slate):**
```bash
docker compose -f compose.test.yml down -v
docker compose -f compose.test.yml up -d formcore-test-db
```

For comprehensive testing documentation, see [Testing Guide](testing.md).

## Linting and Formatting

```bash
# Run linter
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Format code (if configured)
ruff format .
```

## Common Development Tasks

### Creating a New Migration

```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "add new field to forms"

# Create empty migration
alembic revision -m "add RLS policy for submissions"
```

### Adding a New Module

1. Create module directory under `app/modules/`
2. Follow the structure: `api/`, `application/`, `domain/`, `infrastructure/`
3. Register router in `app/main.py`
4. Add domain entities, repositories, and services
5. Write tests

### Testing RLS

When testing endpoints that use RLS:

1. Create test users and workspaces
2. Set up workspace membership
3. Include `X-Workspace-ID` header in test requests
4. Verify users cannot access other workspaces' data

Example test:

```python
def test_workspace_isolation(client, user_token, workspace_id, other_workspace_id):
    # Should succeed
    response = client.get(
        f"/api/v1/workspaces/{workspace_id}/forms",
        headers={
            "Authorization": f"Bearer {user_token}",
            "X-Workspace-ID": str(workspace_id)
        }
    )
    assert response.status_code == 200

    # Should fail (user not member of other workspace)
    response = client.get(
        f"/api/v1/workspaces/{other_workspace_id}/forms",
        headers={
            "Authorization": f"Bearer {user_token}",
            "X-Workspace-ID": str(other_workspace_id)
        }
    )
    assert response.status_code == 403  # Or 404, depending on RLS policy
```

## Debugging

### Database Queries

Enable SQL query logging:

```env
DATABASE_ECHO=true
```

This will print all SQL queries to the console.

### RLS Context

To debug RLS issues, check that session variables are set:

```python
# In a database session
db.execute(text("SELECT current_setting('app.user_id', true)"))
db.execute(text("SELECT current_setting('app.workspace_id', true)"))
```

### Request Logging

All requests are logged with user context via `auth_logging_middleware`. Check logs for:

- User ID
- Workspace ID
- Request path and method
- Response status

## Development with Docker

When using Docker Compose for development, a `compose.override.yml` file is included that adds pgAdmin for database management.

### pgAdmin Setup

The pgAdmin service is automatically started when you run `docker compose up` in development. It provides a web-based interface for managing your PostgreSQL database.

**Access pgAdmin:**
- URL: http://localhost:5050 (or your configured `PGADMIN_PORT`)
- Email: `admin@formcore.com` (or your configured `PGADMIN_EMAIL`)
- Password: `admin` (or your configured `PGADMIN_PASSWORD`)

**Connecting to the Database in pgAdmin:**

1. Log in to pgAdmin
2. Right-click "Servers" → "Register" → "Server"
3. In the "General" tab:
   - Name: `FormCore Development`
4. In the "Connection" tab:
   - Host name/address: `formcore-db` (the Docker service name)
   - Port: `5432`
   - Maintenance database: `formcore` (or your `DATABASE_NAME`)
   - Username: `postgres` (or your `DATABASE_USER`)
   - Password: `postgres` (or your `DATABASE_PASSWORD`)
5. Click "Save"

**Note:** The `compose.override.yml` file is committed to the repository for team sharing, but it only affects local development. It will not be used in production deployments. If you need to customize pgAdmin settings, you can override them in your local `.env` file.

## IDE Setup

### VS Code

Recommended extensions:

- Python
- Pylance
- Ruff (for linting)

### PyCharm

Configure:

- Python interpreter (3.12+)
- Database connection (PostgreSQL)
- Run configuration for `uvicorn app.main:app --reload`
