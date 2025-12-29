"""Enable RLS and create workspace isolation policies.

Revision ID: 002
Revises: 001
Create Date: 2024-12-28

This migration enables Row-Level Security (RLS) on all workspace-scoped tables
and creates policies that enforce workspace membership checks using PostgreSQL
session variables set by the application middleware.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable RLS and create policies for workspace isolation."""

    # Enable and FORCE RLS on workspace-scoped tables
    # FORCE ensures RLS applies even to superusers (critical for test environments)
    op.execute("ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workspaces FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workspace_members ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workspace_members FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE folders ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE folders FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE forms ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE forms FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE form_versions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE form_versions FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE form_fields ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE form_fields FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE form_field_choices ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE form_field_choices FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE submissions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE submissions FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE answers ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE answers FORCE ROW LEVEL SECURITY")

    # === Workspaces policy ===
    # Users can only see workspaces they are members of
    # Note: workspace_id context not required for listing workspaces
    op.execute("""
        CREATE POLICY workspaces_isolation ON workspaces
        FOR ALL
        USING (
            id IN (
                SELECT workspace_id FROM workspace_members
                WHERE user_id = current_setting('app.user_id')::uuid
            )
        )
    """)

    # === Workspace members policy ===
    # Users can only see memberships for the active workspace context
    # AND they must be a member of that workspace
    # This prevents cross-workspace leakage (e.g., seeing Workspace B members
    # when X-Workspace-ID is set to Workspace A)
    # Note: We use a direct check instead of EXISTS to avoid circular dependency
    # The policy allows seeing all members of a workspace if you're querying
    # that workspace AND you have a membership row for it (checked via direct user_id match)
    op.execute("""
        CREATE POLICY workspace_members_isolation ON workspace_members
        FOR ALL
        USING (
            workspace_id = current_setting('app.workspace_id')::uuid
            AND EXISTS (
                SELECT 1 FROM workspace_members wm
                WHERE wm.workspace_id = workspace_members.workspace_id
                  AND wm.user_id = current_setting('app.user_id')::uuid
            )
        )
    """)

    # === Folders policy ===
    # Users can only access folders in workspaces they are members of
    # AND the folder's workspace matches the requested workspace context
    op.execute("""
        CREATE POLICY folders_workspace_isolation ON folders
        FOR ALL
        USING (
            workspace_id = current_setting('app.workspace_id')::uuid
            AND EXISTS (
                SELECT 1 FROM workspace_members
                WHERE workspace_id = folders.workspace_id
                  AND user_id = current_setting('app.user_id')::uuid
            )
        )
    """)

    # === Forms policy ===
    # Users can only access forms in workspaces they are members of
    # AND the form's workspace matches the requested workspace context
    op.execute("""
        CREATE POLICY forms_workspace_isolation ON forms
        FOR ALL
        USING (
            workspace_id = current_setting('app.workspace_id')::uuid
            AND EXISTS (
                SELECT 1 FROM workspace_members
                WHERE workspace_id = forms.workspace_id
                  AND user_id = current_setting('app.user_id')::uuid
            )
        )
    """)

    # === Form versions policy ===
    # Users can only access form versions for forms they can access
    op.execute("""
        CREATE POLICY form_versions_workspace_isolation ON form_versions
        FOR ALL
        USING (
            form_id IN (
                SELECT id FROM forms
                WHERE workspace_id = current_setting('app.workspace_id')::uuid
                  AND EXISTS (
                      SELECT 1 FROM workspace_members
                      WHERE workspace_id = forms.workspace_id
                        AND user_id = current_setting('app.user_id')::uuid
                  )
            )
        )
    """)

    # === Form fields policy ===
    # Users can only access form fields for versions they can access
    op.execute("""
        CREATE POLICY form_fields_workspace_isolation ON form_fields
        FOR ALL
        USING (
            version_id IN (
                SELECT id FROM form_versions
                WHERE form_id IN (
                    SELECT id FROM forms
                    WHERE workspace_id = current_setting('app.workspace_id')::uuid
                      AND EXISTS (
                          SELECT 1 FROM workspace_members
                          WHERE workspace_id = forms.workspace_id
                            AND user_id = current_setting('app.user_id')::uuid
                      )
                )
            )
        )
    """)

    # === Form field choices policy ===
    # Users can only access choices for fields they can access
    op.execute("""
        CREATE POLICY form_field_choices_workspace_isolation ON form_field_choices
        FOR ALL
        USING (
            field_id IN (
                SELECT id FROM form_fields
                WHERE version_id IN (
                    SELECT id FROM form_versions
                    WHERE form_id IN (
                        SELECT id FROM forms
                        WHERE workspace_id = current_setting('app.workspace_id')::uuid
                          AND EXISTS (
                              SELECT 1 FROM workspace_members
                              WHERE workspace_id = forms.workspace_id
                                AND user_id = current_setting('app.user_id')::uuid
                          )
                    )
                )
            )
        )
    """)

    # === Submissions policy ===
    # Users can only access submissions in workspaces they are members of
    # AND the submission's workspace matches the requested workspace context
    op.execute("""
        CREATE POLICY submissions_workspace_isolation ON submissions
        FOR ALL
        USING (
            workspace_id = current_setting('app.workspace_id')::uuid
            AND EXISTS (
                SELECT 1 FROM workspace_members
                WHERE workspace_id = submissions.workspace_id
                  AND user_id = current_setting('app.user_id')::uuid
            )
        )
    """)

    # === Answers policy ===
    # Users can only access answers for submissions they can access
    op.execute("""
        CREATE POLICY answers_workspace_isolation ON answers
        FOR ALL
        USING (
            submission_id IN (
                SELECT id FROM submissions
                WHERE workspace_id = current_setting('app.workspace_id')::uuid
                  AND EXISTS (
                      SELECT 1 FROM workspace_members
                      WHERE workspace_id = submissions.workspace_id
                        AND user_id = current_setting('app.user_id')::uuid
                  )
            )
        )
    """)


def downgrade() -> None:
    """Drop RLS policies and disable RLS."""

    # Drop policies
    op.execute("DROP POLICY IF EXISTS workspaces_isolation ON workspaces")
    op.execute("DROP POLICY IF EXISTS workspace_members_isolation ON workspace_members")
    op.execute("DROP POLICY IF EXISTS folders_workspace_isolation ON folders")
    op.execute("DROP POLICY IF EXISTS forms_workspace_isolation ON forms")
    op.execute(
        "DROP POLICY IF EXISTS form_versions_workspace_isolation ON form_versions"
    )
    op.execute("DROP POLICY IF EXISTS form_fields_workspace_isolation ON form_fields")
    op.execute(
        "DROP POLICY IF EXISTS form_field_choices_workspace_isolation ON form_field_choices"
    )
    op.execute("DROP POLICY IF EXISTS submissions_workspace_isolation ON submissions")
    op.execute("DROP POLICY IF EXISTS answers_workspace_isolation ON answers")

    # Disable RLS
    op.execute("ALTER TABLE answers DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE submissions DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE form_field_choices DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE form_fields DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE form_versions DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE forms DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE folders DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workspace_members DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workspaces DISABLE ROW LEVEL SECURITY")
