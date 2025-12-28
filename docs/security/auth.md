# Authentication

## JWT Tokens

FormCore uses JWT (JSON Web Tokens) for authentication. Tokens are signed with `JWT_SECRET_KEY` using the `HS256` algorithm.

### Token Structure

Tokens contain:

- `user_id`: UUID of the authenticated user
- `email`: User's email address
- `exp`: Expiration timestamp
- `iat`: Issued at timestamp
- `type`: Token type (`access` or `refresh`)

### Token Types

1. **Access tokens**: Short-lived (default: 30 minutes), used for API requests
2. **Refresh tokens**: Long-lived (default: 7 days), used to obtain new access tokens

### Obtaining Tokens

**Register a new user:**

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure-password"
}
```

**Login:**

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure-password"
}
```

Response includes both `access_token` and `refresh_token`.

**Refresh access token:**

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "your-refresh-token"
}
```

## Using Tokens

Include the access token in the `Authorization` header:

```http
Authorization: Bearer <access-token>
```

## Workspace Context

All authenticated requests (except workspace creation) must include the `X-Workspace-ID` header:

```http
X-Workspace-ID: <workspace-uuid>
```

This header is required because:

- RLS policies need to know which workspace to scope queries to
- Users can be members of multiple workspaces
- The workspace ID determines data isolation boundaries

## Identity Object

The `get_current_user` dependency returns an `Identity` object containing:

- `user_id`: UUID
- `email`: String

This identity is used throughout the application for:

- RLS context (`app.user_id` session variable)
- Audit logging
- Permission checks

## Future: API Keys

For server-to-server integrations, API keys may be added in the future. These would work similarly to JWT tokens but with longer expiration times and workspace-scoped permissions.
