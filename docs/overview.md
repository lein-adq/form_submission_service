# Overview

FormCore is a Form Backend-as-a-Service (FBaaS) that provides multi-tenant form management with strong security guarantees through PostgreSQL Row-Level Security (RLS).

## Core Concepts

### Workspaces

Workspaces are the primary tenancy boundary. All forms, folders, and submissions belong to a workspace. Users can be members of multiple workspaces with different roles (owner, admin, editor, viewer).

**Key points:**

- Every authenticated API request must include the `X-Workspace-ID` header
- Workspace membership determines what data a user can access
- Workspaces are isolated from each other at the database level via RLS

### Row-Level Security (RLS)

**RLS is authoritative.** FastAPI does not enforce authorization; PostgreSQL RLS policies do. This means:

- Even if application code has a bug, RLS prevents unauthorized data access
- All database queries are automatically scoped to the user's workspace membership
- RLS policies use PostgreSQL session variables (`app.user_id` and `app.workspace_id`) set by middleware

**How it works:**

1. Middleware extracts `user_id` from JWT token and `workspace_id` from `X-Workspace-ID` header
2. These values are set as PostgreSQL session variables before each request
3. RLS policies use these variables to filter rows automatically
4. Application code uses `get_db_with_rls_context` dependency to get a scoped database session

### Forms and Versions

Forms follow a versioned model similar to Typeform:

- **Forms** are containers that hold multiple versions
- **Form Versions** are immutable snapshots of form definitions (fields, validation rules, etc.)
- Each form has a `draft_version_id` (work in progress) and `published_version_id` (live version)
- Only published forms can accept submissions
- Submissions are tied to a specific version, enabling form evolution without breaking historical data

### Submissions

Submissions can be created in two ways:

1. **Public submissions** (no authentication): Use the service role database connection to bypass RLS. Only works for published forms.
2. **Authenticated submissions** (requires JWT): Uses RLS to ensure submissions are scoped to the correct workspace.

All submissions are denormalized with `workspace_id` for efficient RLS filtering.
