# Architecture

FormCore follows a **hexagonal architecture** (ports and adapters) with clear separation between domain, application, and infrastructure layers.

## Module Structure

Each feature module (`auth`, `workspaces`, `forms`, `submissions`) follows the same structure:

```
modules/{module}/
├── api/              # FastAPI routers and request/response schemas
├── application/      # Use cases, commands, handlers, services
├── domain/           # Entities, value objects, policies, repository interfaces
└── infrastructure/   # PostgreSQL repository implementations
```

## Core Layer

The `core/` directory contains shared infrastructure:

- **`config/`**: Settings and environment variable management
- **`db/`**: Database models, session management, RLS utilities, migrations
- **`domain/`**: Shared domain concepts (Identity, permissions, value objects)
- **`security/`**: JWT handling, password hashing, identity management
- **`middleware/`**: RLS middleware, auth logging, rate limiting
- **`dependencies.py`**: FastAPI dependencies (auth, database, workspace context)

## Data Flow

### Authenticated Request Flow

1. **Request arrives** → FastAPI router
2. **Middleware** (`rls_middleware`) extracts JWT and `X-Workspace-ID` header
3. **Dependencies** (`get_current_user`, `get_workspace_id`) validate and parse
4. **Database dependency** (`get_db_with_rls_context`) applies RLS session variables
5. **Service layer** executes business logic using domain entities
6. **Repository** (infrastructure) performs database operations (automatically filtered by RLS)
7. **Response** returned to client

### Public Submission Flow

1. **Request arrives** at `/api/v1/forms/{form_id}/submissions` (no auth required)
2. **Service dependency** uses `get_service_db()` (bypasses RLS)
3. **Service** validates form is published
4. **Repository** creates submission using service role connection
5. **Response** returned

## Key Design Decisions

- **RLS-first security**: Authorization happens at the database layer, not application layer
- **Domain-driven design**: Business logic lives in domain entities and services, not in API routers
- **Repository pattern**: Database access is abstracted behind interfaces, enabling testing and future database support
- **Command pattern**: Use cases are modeled as commands handled by services
- **Value objects**: Strong typing for IDs (UserId, WorkspaceId, FormId) prevents mixing them up
