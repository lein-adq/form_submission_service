# Docker Deployment

## Quick Start

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

4. **Check service status**

   ```bash
   docker compose ps
   ```

5. **View logs**

   ```bash
   docker compose logs -f formcore-backend
   ```

6. **Access the application**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## Services

- **formcore-db**: PostgreSQL 16 database
- **formcore-backend**: FastAPI application

## Database Migrations

Migrations run automatically on container startup via `scripts/start.sh`. The script:

1. Waits for the database to be ready
2. Runs Alembic migrations (`alembic upgrade head`)
3. Starts the FastAPI application

## Stopping Services

```bash
# Stop services
docker compose down

# Stop and remove volumes (⚠️ deletes database data)
docker compose down -v
```

## Environment Variables

See [Configuration](../configuration.md) for detailed environment variable documentation.

Key variables:

- `DATABASE_USER`: PostgreSQL username (default: `postgres`)
- `DATABASE_PASSWORD`: PostgreSQL password (**change in production!**)
- `DATABASE_NAME`: Database name (default: `formcore`)
- `JWT_SECRET_KEY`: Secret key for JWT tokens (**change in production!**)
- `CORS_ORIGINS`: JSON array of allowed origins (default: `["http://localhost:3000", "http://localhost:8000"]`)

## Troubleshooting

### Database not ready

If migrations fail, ensure the database healthcheck passes:

```bash
docker compose ps formcore-db
```

### Port conflicts

If ports 8000 or 5432 are in use, change them in `.env`:

```
BACKEND_PORT=8001
DATABASE_PORT=5433
```

### View database logs

```bash
docker compose logs formcore-db
```
