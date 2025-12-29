"""Secure RLS policies with system bypass and FORCE RLS.

Revision ID: 003
Revises: 002
Create Date: 2025-12-28 20:45:00

"""

from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0. CRITICAL: FORCE RLS on all tables
    # This forces the 'postgres' superuser to obey RLS.
    tables = [
        "workspaces",
        "workspace_members",
        "folders",
        "forms",
        "form_versions",
        "form_fields",
        "form_field_choices",
        "submissions",
        "answers",
    ]
    for table in tables:
        # Enable isn't enough for superusers; we need FORCE
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")

    # 1. Workspaces Policy
    op.execute("DROP POLICY IF EXISTS workspaces_isolation ON workspaces")
    op.execute("""
        CREATE POLICY workspaces_isolation ON workspaces
        FOR ALL
        USING (
            current_setting('app.bypass_rls', true) = 'on'
            OR (
                current_setting('app.user_id', true) IS NOT NULL
                AND id IN (
                    SELECT workspace_id FROM workspace_members
                    WHERE user_id = current_setting('app.user_id')::uuid
                )
            )
        )
    """)

    # 2. Folders Policy
    op.execute("DROP POLICY IF EXISTS folders_workspace_isolation ON folders")
    op.execute("""
        CREATE POLICY folders_workspace_isolation ON folders
        FOR ALL
        USING (
            current_setting('app.bypass_rls', true) = 'on'
            OR (
                current_setting('app.user_id', true) IS NOT NULL
                AND current_setting('app.workspace_id', true) IS NOT NULL
                AND workspace_id = current_setting('app.workspace_id')::uuid
                AND EXISTS (
                    SELECT 1 FROM workspace_members
                    WHERE workspace_id = folders.workspace_id
                    AND user_id = current_setting('app.user_id')::uuid
                )
            )
        )
    """)

    # 3. Forms Policy
    op.execute("DROP POLICY IF EXISTS forms_workspace_isolation ON forms")
    op.execute("""
        CREATE POLICY forms_workspace_isolation ON forms
        FOR ALL
        USING (
            current_setting('app.bypass_rls', true) = 'on'
            OR (
                current_setting('app.user_id', true) IS NOT NULL
                AND current_setting('app.workspace_id', true) IS NOT NULL
                AND workspace_id = current_setting('app.workspace_id')::uuid
                AND EXISTS (
                    SELECT 1 FROM workspace_members
                    WHERE workspace_id = forms.workspace_id
                    AND user_id = current_setting('app.user_id')::uuid
                )
            )
        )
    """)

    # 4. Form Versions Policy
    op.execute(
        "DROP POLICY IF EXISTS form_versions_workspace_isolation ON form_versions"
    )
    op.execute("""
        CREATE POLICY form_versions_workspace_isolation ON form_versions
        FOR ALL
        USING (
            current_setting('app.bypass_rls', true) = 'on'
            OR (
                current_setting('app.user_id', true) IS NOT NULL
                AND current_setting('app.workspace_id', true) IS NOT NULL
                AND form_id IN (
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

    # 5. Form Fields Policy
    op.execute("DROP POLICY IF EXISTS form_fields_workspace_isolation ON form_fields")
    op.execute("""
        CREATE POLICY form_fields_workspace_isolation ON form_fields
        FOR ALL
        USING (
            current_setting('app.bypass_rls', true) = 'on'
            OR (
                current_setting('app.user_id', true) IS NOT NULL
                AND current_setting('app.workspace_id', true) IS NOT NULL
                AND version_id IN (
                    SELECT id FROM form_versions WHERE form_id IN (
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

    # 6. Form Field Choices Policy
    op.execute(
        "DROP POLICY IF EXISTS form_field_choices_workspace_isolation ON form_field_choices"
    )
    op.execute("""
        CREATE POLICY form_field_choices_workspace_isolation ON form_field_choices
        FOR ALL
        USING (
            current_setting('app.bypass_rls', true) = 'on'
            OR (
                current_setting('app.user_id', true) IS NOT NULL
                AND current_setting('app.workspace_id', true) IS NOT NULL
                AND field_id IN (
                    SELECT id FROM form_fields WHERE version_id IN (
                        SELECT id FROM form_versions WHERE form_id IN (
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
        )
    """)

    # 7. Submissions Policy
    op.execute("DROP POLICY IF EXISTS submissions_workspace_isolation ON submissions")
    op.execute("""
        CREATE POLICY submissions_workspace_isolation ON submissions
        FOR ALL
        USING (
            current_setting('app.bypass_rls', true) = 'on'
            OR
            current_setting('app.is_public_insert', true) = 'true'
            OR
            (
                current_setting('app.user_id', true) IS NOT NULL
                AND current_setting('app.workspace_id', true) IS NOT NULL
                AND workspace_id = current_setting('app.workspace_id')::uuid
                AND EXISTS (
                    SELECT 1 FROM workspace_members
                    WHERE workspace_id = submissions.workspace_id
                    AND user_id = current_setting('app.user_id')::uuid
                )
            )
        )
    """)

    # 8. Answers Policy
    op.execute("DROP POLICY IF EXISTS answers_workspace_isolation ON answers")
    op.execute("""
        CREATE POLICY answers_workspace_isolation ON answers
        FOR ALL
        USING (
            current_setting('app.bypass_rls', true) = 'on'
            OR
            current_setting('app.is_public_insert', true) = 'true'
            OR
            (
                current_setting('app.user_id', true) IS NOT NULL
                AND current_setting('app.workspace_id', true) IS NOT NULL
                AND submission_id IN (
                    SELECT id FROM submissions
                    WHERE workspace_id = current_setting('app.workspace_id')::uuid
                    AND EXISTS (
                        SELECT 1 FROM workspace_members
                        WHERE workspace_id = submissions.workspace_id
                        AND user_id = current_setting('app.user_id')::uuid
                    )
                )
            )
        )
    """)


def downgrade() -> None:
    # Simplified downgrade
    op.execute("DROP POLICY IF EXISTS answers_workspace_isolation ON answers")
    op.execute("DROP POLICY IF EXISTS submissions_workspace_isolation ON submissions")
    op.execute(
        "DROP POLICY IF EXISTS form_field_choices_workspace_isolation ON form_field_choices"
    )
    op.execute("DROP POLICY IF EXISTS form_fields_workspace_isolation ON form_fields")
    op.execute(
        "DROP POLICY IF EXISTS form_versions_workspace_isolation ON form_versions"
    )
    op.execute("DROP POLICY IF EXISTS forms_workspace_isolation ON forms")
    op.execute("DROP POLICY IF EXISTS folders_workspace_isolation ON folders")
    op.execute("DROP POLICY IF EXISTS workspaces_isolation ON workspaces")
