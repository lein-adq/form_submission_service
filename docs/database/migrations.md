# Database Migrations

FormCore uses [Alembic](https://alembic.sqlalchemy.org/) for database migrations.

## Automatic Migrations

Migrations run automatically on container startup via `scripts/start.sh`. The script:

1. Waits for the database to be ready
2. Runs `alembic upgrade head`
3. Starts the FastAPI application

## Manual Migration Commands

### Running Migrations

```bash
# Enter the backend container
docker compose exec formcore-backend bash

# Run all pending migrations
alembic upgrade head

# Run migrations to a specific revision
alembic upgrade <revision>

# Rollback one migration
alembic downgrade -1
```

### Creating Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Create empty migration (for data migrations or RLS policies)
alembic revision -m "description of changes"
```

### Migration Files

Migrations are stored in `app/core/db/migrations/versions/` with naming pattern:

```
{timestamp}_{revision_id}_{description}.py
```

## RLS Policies in Migrations

RLS policies should be added in migrations, not in application code. Example:

```python
def upgrade() -> None:
    # Enable RLS on table
    op.execute("ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY")

    # Create policy
    op.execute("""
        CREATE POLICY workspace_isolation ON workspaces
        FOR ALL
        USING (
            id IN (
                SELECT workspace_id FROM workspace_members
                WHERE user_id = current_setting('app.user_id')::uuid
            )
        )
    """)
```

## Best Practices

1. **Always test migrations** on a copy of production data before applying
2. **Review auto-generated migrations** - Alembic may miss some changes
3. **Use transactions** - Alembic runs migrations in transactions by default
4. **Document RLS policies** - Add comments explaining policy logic
5. **Version control** - Never edit existing migration files; create new ones

## Migration History

View migration history:

```bash
alembic history
```

View current database revision:

```bash
alembic current
```
