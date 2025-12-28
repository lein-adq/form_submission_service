"""Initial schema with Typeform-class design.

Revision ID: 001
Revises:
Create Date: 2024-12-28

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === Users table ===
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # === Workspaces table ===
    op.create_table(
        "workspaces",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # === Workspace members table ===
    op.create_table(
        "workspace_members",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("workspace_id", "user_id"),
    )
    op.create_index("ix_workspace_members_user_id", "workspace_members", ["user_id"])

    # === Folders table (self-referential for nesting) ===
    op.create_table(
        "folders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["folders.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_folders_workspace_id", "folders", ["workspace_id"])
    op.create_index("ix_folders_parent_id", "folders", ["parent_id"])

    # === Forms table (container) ===
    op.create_table(
        "forms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("folder_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("draft_version_id", sa.Uuid(), nullable=True),
        sa.Column("published_version_id", sa.Uuid(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["folder_id"],
            ["folders.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_forms_workspace_id", "forms", ["workspace_id"])
    op.create_index("ix_forms_folder_id", "forms", ["folder_id"])

    # === Form versions table (definition snapshots) ===
    op.create_table(
        "form_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("form_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(), nullable=False, server_default="draft"),
        sa.Column(
            "definition_jsonb",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["form_id"],
            ["forms.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_form_versions_form_id", "form_versions", ["form_id"])
    op.create_unique_constraint(
        "uq_form_versions_form_version",
        "form_versions",
        ["form_id", "version_number"],
    )

    # === Add FK from forms to form_versions (deferred due to circular ref) ===
    op.create_foreign_key(
        "fk_forms_draft_version",
        "forms",
        "form_versions",
        ["draft_version_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_forms_published_version",
        "forms",
        "form_versions",
        ["published_version_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # === Form fields table (extracted for querying) ===
    op.create_table(
        "form_fields",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("version_id", sa.Uuid(), nullable=False),
        sa.Column("ref", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["version_id"],
            ["form_versions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_form_fields_version_id", "form_fields", ["version_id"])
    op.create_unique_constraint(
        "uq_form_fields_version_ref",
        "form_fields",
        ["version_id", "ref"],
    )

    # === Form field choices table ===
    op.create_table(
        "form_field_choices",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("field_id", sa.Uuid(), nullable=False),
        sa.Column("choice_id", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["field_id"],
            ["form_fields.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_form_field_choices_field_id", "form_field_choices", ["field_id"]
    )
    op.create_unique_constraint(
        "uq_form_field_choices_field_choice",
        "form_field_choices",
        ["field_id", "choice_id"],
    )

    # === Submissions table ===
    op.create_table(
        "submissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("form_id", sa.Uuid(), nullable=False),
        sa.Column("form_version_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),  # Denormalized for RLS
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["form_id"],
            ["forms.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["form_version_id"],
            ["form_versions.id"],
            ondelete="RESTRICT",  # Prevent deleting versions with submissions
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_submissions_form_id", "submissions", ["form_id"])
    op.create_index(
        "ix_submissions_form_version_id", "submissions", ["form_version_id"]
    )
    op.create_index("ix_submissions_workspace_id", "submissions", ["workspace_id"])

    # === Answers table ===
    op.create_table(
        "answers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("submission_id", sa.Uuid(), nullable=False),
        sa.Column("field_ref", sa.String(), nullable=False),
        sa.Column("field_type", sa.String(), nullable=False),
        sa.Column(
            "value_jsonb",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_number", sa.Float(), nullable=True),
        sa.Column("value_bool", sa.Boolean(), nullable=True),
        sa.Column("value_time", sa.DateTime(), nullable=True),
        sa.Column("choice_ids", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["submission_id"],
            ["submissions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_answers_submission_id", "answers", ["submission_id"])
    op.create_index("ix_answers_field_ref", "answers", ["field_ref"])


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_table("answers")
    op.drop_table("submissions")
    op.drop_table("form_field_choices")
    op.drop_table("form_fields")

    # Drop FK constraints from forms to form_versions before dropping form_versions
    op.drop_constraint("fk_forms_draft_version", "forms", type_="foreignkey")
    op.drop_constraint("fk_forms_published_version", "forms", type_="foreignkey")

    op.drop_table("form_versions")
    op.drop_table("forms")
    op.drop_table("folders")
    op.drop_table("workspace_members")
    op.drop_table("workspaces")
    op.drop_table("users")
