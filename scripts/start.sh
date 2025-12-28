#!/bin/bash
set -e

echo "Waiting for database to be ready..."
# Wait for PostgreSQL to be ready
until PGPASSWORD="${DATABASE_PASSWORD}" psql -h "${DATABASE_HOST:-formcore-db}" -U "${DATABASE_USER}" -d "${DATABASE_NAME}" -c '\q' 2>/dev/null; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "Database is ready!"

# Run migrations
echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
