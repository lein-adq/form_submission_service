# Row-Level Security (RLS)

## Philosophy

**FastAPI does not enforce authorization; Postgres RLS does.**

This is a critical architectural decision. Even if application code has bugs or is bypassed, RLS policies at the database level ensure data isolation. This defense-in-depth approach is essential for multi-tenant systems.

## How RLS Works in FormCore

### Session Variables

RLS policies use PostgreSQL session variables set before each request:

- `app.user_id`: The authenticated user's UUID (from JWT token)
- `app.workspace_id`: The workspace context (from `X-Workspace-ID` header)

These are set by `app.core.db.rls.apply_rls_context()` which is called by the `get_db_with_rls_context` dependency.

### Middleware Flow

1. `rls_middleware` extracts `user_id` from JWT Bearer token
2. `rls_middleware` extracts `workspace_id` from `X-Workspace-ID` header
3. Values are stored in `request.state` for use by dependencies
4. `get_db_with_rls_context` dependency calls `apply_rls_context()` to set PostgreSQL session variables
5. All subsequent queries in that request are automatically filtered by RLS policies

### RLS Policies

RLS policies are defined in database migrations. They typically check:

- User is a member of the workspace (via `workspace_members` table)
- Resource belongs to the workspace (via `workspace_id` foreign key)
- User has appropriate role/permissions for the operation

**Example policy pattern:**

```sql
CREATE POLICY workspace_isolation ON workspaces
  FOR ALL
  USING (
    id IN (
      SELECT workspace_id FROM workspace_members
      WHERE user_id = current_setting('app.user_id')::uuid
    )
  );
```

## Threat Model Notes

### What RLS Protects Against

- Application bugs that forget to check workspace membership
- SQL injection that attempts to access other workspaces
- Direct database access (if credentials are compromised, RLS still enforces isolation)
- Race conditions in application-level authorization checks

### What RLS Does NOT Protect Against

- Missing `X-Workspace-ID` header (application should validate this)
- Invalid JWT tokens (handled by `get_current_user` dependency)
- Rate limiting (handled by middleware)
- Input validation (handled by Pydantic schemas)

## Service Role (Bypassing RLS)

For public form submissions, we use a separate database connection with a service role that bypasses RLS. This is configured via `DATABASE_SERVICE_URL`.

**Important:** The service role should only be used for:

- Public submission creation (validated at application level)
- Administrative operations (future: admin endpoints)

Never use the service role for authenticated user operations.

## Testing RLS

When writing tests, ensure you:

1. Set up proper workspace membership
2. Include `X-Workspace-ID` header in requests
3. Use valid JWT tokens
4. Test that users cannot access other workspaces' data
