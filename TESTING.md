# Testing Quick Reference

## Run Tests in Docker (Recommended)

```bash
# Start test database
docker compose -f compose.test.yml up -d formcore-test-db

# Run all tests
docker compose -f compose.test.yml run --rm formcore-test pytest

# Run with coverage
docker compose -f compose.test.yml run --rm formcore-test pytest --cov=app --cov-report=html --cov-report=term

# Run specific tests
docker compose -f compose.test.yml run --rm formcore-test pytest tests/modules/auth/

# Unit tests only
docker compose -f compose.test.yml run --rm formcore-test pytest tests/modules/ -k "test_services or test_repositories"

# E2E tests only
docker compose -f compose.test.yml run --rm formcore-test pytest tests/modules/ -k "test_api"

# Clean up
docker compose -f compose.test.yml down -v
```

## View Coverage Report

After running tests with coverage:

```bash
# Coverage HTML is generated in htmlcov/ directory
# Open htmlcov/index.html in your browser
```

## Database Management

```bash
# Reset test database
docker compose -f compose.test.yml down -v
docker compose -f compose.test.yml up -d formcore-test-db

# Run migrations in container
docker compose -f compose.test.yml run --rm formcore-test alembic upgrade head
```

## Full Documentation

See [docs/testing.md](docs/testing.md) for complete testing guide.
