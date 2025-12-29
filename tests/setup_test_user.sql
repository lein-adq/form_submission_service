-- 1. Create the application user if it doesn't exist
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'app_user') THEN
      CREATE ROLE app_user LOGIN PASSWORD 'app_password';
   END IF;
END
$do$;

-- 2. Grant access to schema, tables, and sequences
-- Note: We grant on public schema. If you use schemas, adjust accordingly.
GRANT USAGE ON SCHEMA public TO app_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- 3. Ensure future tables created by postgres are accessible to app_user
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO app_user;