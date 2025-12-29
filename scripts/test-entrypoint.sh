#!/bin/bash
# Entrypoint script for test container

set -e

echo "Waiting for database..."
while ! pg_isready -h formcore-test-db -U postgres > /dev/null 2>&1; do
    sleep 1
done
echo "Database is ready!"

echo "Running migrations..."
alembic upgrade head

echo "Setting up non-privileged app_user for RLS testing..."
# We use PGPASSWORD to authenticate as postgres (superuser) to run this setup
export PGPASSWORD=${POSTGRES_PASSWORD:-postgres}
psql -h formcore-test-db -U postgres -d formcore_test -f /app/tests/setup_test_user.sql

# NOW, we switch the environment variable to the non-privileged user
# This environment variable override will only affect the pytest process below
export DATABASE_URL="postgresql://app_user:app_password@formcore-test-db:5432/formcore_test"
echo "Switched DATABASE_URL to non-privileged user: app_user"

echo "Ready to run tests!"
exec "$@"