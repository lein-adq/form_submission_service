# Configuration

FormCore is configured via environment variables. You can use a `.env` file for local development, but in production, use your platform's environment variable management.

## Database

| Variable               | Default                                                  | Description                                                   |
| ---------------------- | -------------------------------------------------------- | ------------------------------------------------------------- |
| `DATABASE_URL`         | `postgresql://postgres:postgres@localhost:5432/formcore` | Primary database connection string                            |
| `DATABASE_ECHO`        | `false`                                                  | Log all SQL queries (useful for debugging)                    |
| `DATABASE_SERVICE_URL` | (none)                                                   | Service role connection for public submissions (bypasses RLS) |
| `DATABASE_USER`        | `postgres`                                               | PostgreSQL username (used in Docker Compose)                  |
| `DATABASE_PASSWORD`    | `postgres`                                               | PostgreSQL password (used in Docker Compose)                  |
| `DATABASE_NAME`        | `formcore`                                               | Database name (used in Docker Compose)                        |
| `DATABASE_PORT`        | `5432`                                                   | Database port (used in Docker Compose)                        |

## JWT Authentication

| Variable                          | Default                                | Description                                                       |
| --------------------------------- | -------------------------------------- | ----------------------------------------------------------------- |
| `JWT_SECRET_KEY`                  | `your-secret-key-change-in-production` | Secret key for signing JWT tokens (**MUST change in production**) |
| `JWT_ALGORITHM`                   | `HS256`                                | JWT signing algorithm                                             |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30`                                   | Access token expiration time in minutes                           |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS`   | `7`                                    | Refresh token expiration time in days                             |

### Generating JWT Secret Key

Use a high-entropy secret for JWT signing:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Important:** Use a different secret than your database password. JWT secrets should be high-entropy random strings, while database passwords can be any secure string.

## CORS

| Variable                 | Default                                              | Description                        |
| ------------------------ | ---------------------------------------------------- | ---------------------------------- |
| `CORS_ORIGINS`           | `["http://localhost:3000", "http://localhost:8000"]` | JSON array of allowed origins      |
| `CORS_ALLOW_CREDENTIALS` | `true`                                               | Allow credentials in CORS requests |
| `CORS_ALLOW_METHODS`     | `["*"]`                                              | Allowed HTTP methods               |
| `CORS_ALLOW_HEADERS`     | `["*"]`                                              | Allowed request headers            |

**Production:** Never use `["*"]` for `CORS_ORIGINS`. Use explicit origins:

```json
["https://yourdomain.com", "https://app.yourdomain.com"]
```

## Environment

| Variable       | Default       | Description                                               |
| -------------- | ------------- | --------------------------------------------------------- |
| `ENVIRONMENT`  | `development` | Environment name (`development`, `staging`, `production`) |
| `DEBUG`        | `false`       | Enable debug mode (more verbose errors)                   |
| `BACKEND_PORT` | `8000`        | Port for FastAPI application (used in Docker Compose)     |

## Example `.env` File

```env
# Database
DATABASE_URL=postgresql://postgres:secure-password@localhost:5432/formcore
DATABASE_ECHO=false

# JWT
JWT_SECRET_KEY=your-high-entropy-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (development)
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
CORS_ALLOW_CREDENTIALS=true

# Environment
ENVIRONMENT=development
DEBUG=true
```

## Production Configuration

In production:

1. **Never commit `.env` files** to version control
2. **Use secret management services** (AWS Secrets Manager, HashiCorp Vault, etc.)
3. **Rotate secrets regularly** (especially `JWT_SECRET_KEY`)
4. **Use different secrets** for each environment
5. **Set `ENVIRONMENT=production`** and `DEBUG=false`

## Validation

Settings are validated on application startup. Invalid values will cause the application to fail fast with clear error messages.
