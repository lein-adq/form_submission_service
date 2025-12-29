# FormCore

A FastAPI-based Form Backend-as-a-Service (FBaaS) with multi-tenant support, Row-Level Security (RLS), and JWT authentication.

## Core Concepts

### Workspace Tenancy

FormCore uses **workspaces** as the primary tenancy boundary. All forms, folders, and submissions belong to a workspace. Users can be members of multiple workspaces with different roles.

**All authenticated API requests must include the `X-Workspace-ID` header** to specify which workspace context to use.

### RLS is Authoritative

**FastAPI does not enforce authorization; Postgres RLS does.** This means even if application code has bugs, RLS policies at the database level ensure data isolation. All database queries are automatically scoped to the user's workspace membership via PostgreSQL session variables.

See [Security: RLS](docs/security/rls.md) for details.

## Quickstart (Docker)

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd form_submission_service
   ```

2. **Create environment file** (optional)

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Build and start services**

   ```bash
   docker compose up -d --build
   ```

4. **Access the application**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## Documentation

- **[Overview](docs/overview.md)** - Core concepts: workspaces, forms, versions, submissions
- **[Architecture](docs/architecture.md)** - Hexagonal structure, module boundaries
- **[Security](docs/security/)** - [RLS policies](docs/security/rls.md) and [authentication](docs/security/auth.md)
- **[Database](docs/database/)** - [Schema](docs/database/schema.md), [migrations](docs/database/migrations.md)
- **[Deployment](docs/deployment/)** - [Docker setup](docs/deployment/docker.md), [production checklist](docs/deployment/production.md)
- **[Development](docs/development.md)** - Local development setup, testing, debugging
- **[Configuration](docs/configuration.md)** - Environment variables reference
- **[API](docs/api.md)** - API concepts and endpoint groups (see `/docs` for interactive API documentation)

## Testing

```bash
# Start test database
docker compose -f compose.test.yml up -d formcore-test-db

# Run tests
docker compose -f compose.test.yml run --rm formcore-test pytest

# With coverage
docker compose -f compose.test.yml run --rm formcore-test pytest --cov=app --cov-report=html
```

See [TESTING.md](TESTING.md) for quick reference or [docs/testing.md](docs/testing.md) for comprehensive guide.

## License

MIT
