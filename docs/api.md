# API Overview

## Base URL

All API endpoints are prefixed with `/api/v1`.

## Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These are auto-generated from your FastAPI code and provide the most up-to-date endpoint documentation.

## Authentication

Most endpoints require authentication via JWT Bearer token:

```http
Authorization: Bearer <access-token>
```

See [Authentication](security/auth.md) for details on obtaining tokens.

## Workspace Context

All authenticated endpoints (except workspace creation) require the `X-Workspace-ID` header:

```http
X-Workspace-ID: <workspace-uuid>
```

This header is required because RLS policies need to know which workspace to scope queries to.

## Endpoint Groups

### Authentication (`/api/v1/auth`)

- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and get tokens
- `POST /auth/refresh` - Refresh access token

### Workspaces (`/api/v1/workspaces`)

- `POST /workspaces` - Create a new workspace
- `GET /workspaces` - List user's workspaces
- `GET /workspaces/{workspace_id}` - Get workspace details
- `POST /workspaces/{workspace_id}/folders` - Create folder
- `GET /workspaces/{workspace_id}/folders` - List folders

### Forms (`/api/v1/forms`)

- `POST /workspaces/{workspace_id}/forms` - Create form
- `GET /workspaces/{workspace_id}/forms` - List forms
- `GET /workspaces/{workspace_id}/forms/{form_id}` - Get form
- `PUT /workspaces/{workspace_id}/forms/{form_id}` - Update form
- `DELETE /workspaces/{workspace_id}/forms/{form_id}` - Delete form
- `POST /workspaces/{workspace_id}/forms/{form_id}/versions` - Create form version
- `GET /workspaces/{workspace_id}/forms/{form_id}/versions` - List versions
- `POST /workspaces/{workspace_id}/forms/{form_id}/publish` - Publish form

### Submissions

**Public endpoint** (no authentication):

- `POST /forms/{form_id}/submissions` - Create submission (public)

**Authenticated endpoints**:

- `GET /workspaces/{workspace_id}/forms/{form_id}/submissions` - List submissions
- `GET /workspaces/{workspace_id}/submissions` - List all workspace submissions
- `GET /workspaces/{workspace_id}/submissions/{submission_id}` - Get submission

## Response Formats

### Success Responses

Most endpoints return JSON with the requested data. Status codes:

- `200 OK` - Successful GET/PUT request
- `201 Created` - Successful POST request
- `204 No Content` - Successful DELETE request

### Error Responses

Errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common status codes:

- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Authenticated but not authorized (RLS blocked access)
- `404 Not Found` - Resource doesn't exist or not accessible
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

## Rate Limiting

API requests are rate-limited. Check response headers:

- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: When the rate limit resets

## Public Submissions

Public form submissions use a different authentication model:

1. **No JWT token required** - Anyone can submit to a published form
2. **Service role database connection** - Bypasses RLS for submission creation
3. **Application-level validation** - Ensures form is published before accepting submission
4. **Workspace isolation** - Submissions are still scoped to the form's workspace

This allows embedding forms in public websites without requiring user authentication.

## Pagination

Currently, list endpoints return all results. Future versions may add pagination with:

- `limit` query parameter
- `offset` or `cursor` query parameter
- Pagination metadata in response

## Versioning

The API is versioned via the `/api/v1` prefix. When breaking changes are introduced, a new version (`/api/v2`) will be created while maintaining backward compatibility with v1.
