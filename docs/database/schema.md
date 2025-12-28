# Database Schema

## Overview

FormCore uses PostgreSQL 16 with the following main tables:

- `users`: User accounts
- `workspaces`: Multi-tenant containers
- `workspace_members`: User-workspace relationships with roles
- `folders`: Hierarchical organization of forms
- `forms`: Form containers
- `form_versions`: Immutable form definition snapshots
- `form_fields`: Extracted fields from form versions (for querying)
- `form_field_choices`: Choice options for fields
- `submissions`: Form submissions
- `answers`: Individual answers within submissions

## Key Design Patterns

### Denormalization for RLS

The `submissions` table includes a `workspace_id` column even though it could be derived from `form_id → forms.workspace_id`. This denormalization enables efficient RLS filtering without joins.

### Versioning

Forms use a versioned model:

- `forms.draft_version_id`: Points to the current work-in-progress version
- `forms.published_version_id`: Points to the live version that accepts submissions
- `form_versions` are immutable once created
- Submissions reference a specific `form_version_id` to preserve historical context

### Soft Deletes

Currently, all deletes are hard deletes (CASCADE). Future versions may add soft deletes with `deleted_at` timestamps.

## Relationships

```
workspaces
  ├── workspace_members (many-to-many with users)
  ├── folders (one-to-many, self-referential for nesting)
  └── forms (one-to-many)
      ├── form_versions (one-to-many)
      │   ├── form_fields (one-to-many)
      │   │   └── form_field_choices (one-to-many)
      │   └── submissions (one-to-many)
      └── submissions (one-to-many, denormalized workspace_id)
          └── answers (one-to-many)
```

## Indexes

Key indexes for performance:

- `users.email` (unique)
- `workspace_members.user_id`
- `forms.workspace_id`
- `submissions.workspace_id` (for RLS)
- `submissions.form_id`
- `answers.submission_id`

See the migration files in `app/core/db/migrations/versions/` for complete schema definitions.
