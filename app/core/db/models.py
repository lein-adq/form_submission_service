"""SQLModel database models matching the Typeform-class schema."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlmodel import Field, Relationship, SQLModel

from app.core.domain.permissions import Role
from app.core.domain.value_objects import FieldType, FormStatus, VersionState


class User(SQLModel, table=True):
    """User model."""

    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False)
    password_hash: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Workspace(SQLModel, table=True):
    """Workspace model."""

    __tablename__ = "workspaces"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    members: list["WorkspaceMember"] = Relationship(
        back_populates="workspace",
        sa_relationship_kwargs={"passive_deletes": True},
    )
    folders: list["Folder"] = Relationship(
        back_populates="workspace",
        sa_relationship_kwargs={"passive_deletes": True},
    )
    forms: list["Form"] = Relationship(
        back_populates="workspace",
        sa_relationship_kwargs={"passive_deletes": True},
    )


class WorkspaceMember(SQLModel, table=True):
    """Workspace membership model."""

    __tablename__ = "workspace_members"

    workspace_id: UUID = Field(foreign_key="workspaces.id", primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", primary_key=True)
    role: Role = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    workspace: Workspace = Relationship(back_populates="members")
    user: User = Relationship()


class Folder(SQLModel, table=True):
    """Folder model for organizing forms within a workspace."""

    __tablename__ = "folders"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    workspace_id: UUID = Field(foreign_key="workspaces.id", index=True, nullable=False)
    name: str = Field(nullable=False)
    parent_id: UUID | None = Field(
        default=None, foreign_key="folders.id", nullable=True
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    workspace: Workspace = Relationship(back_populates="folders")
    parent: Optional["Folder"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "Folder.id"},
    )
    children: list["Folder"] = Relationship(back_populates="parent")
    forms: list["Form"] = Relationship(back_populates="folder")


class Form(SQLModel, table=True):
    """Form container model."""

    __tablename__ = "forms"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    workspace_id: UUID = Field(foreign_key="workspaces.id", index=True, nullable=False)
    folder_id: UUID | None = Field(
        default=None, foreign_key="folders.id", nullable=True
    )
    name: str = Field(nullable=False)
    status: FormStatus = Field(default=FormStatus.DRAFT, nullable=False)
    draft_version_id: UUID | None = Field(default=None, nullable=True)
    published_version_id: UUID | None = Field(default=None, nullable=True)
    created_by: UUID | None = Field(default=None, foreign_key="users.id", nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    workspace: Workspace = Relationship(back_populates="forms")
    folder: Folder | None = Relationship(back_populates="forms")
    creator: User | None = Relationship()
    versions: list["FormVersion"] = Relationship(back_populates="form")
    submissions: list["Submission"] = Relationship(back_populates="form")


class FormVersion(SQLModel, table=True):
    """Form version model storing definition snapshots."""

    __tablename__ = "form_versions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    form_id: UUID = Field(foreign_key="forms.id", index=True, nullable=False)
    version_number: int = Field(nullable=False)
    state: VersionState = Field(default=VersionState.DRAFT, nullable=False)
    definition_jsonb: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSONB, nullable=False)
    )
    created_by: UUID | None = Field(default=None, foreign_key="users.id", nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    form: Form = Relationship(back_populates="versions")
    creator: User | None = Relationship()
    fields: list["FormField"] = Relationship(back_populates="version")
    submissions: list["Submission"] = Relationship(back_populates="form_version")


class FormField(SQLModel, table=True):
    """Form field model extracted from definition for querying."""

    __tablename__ = "form_fields"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    version_id: UUID = Field(foreign_key="form_versions.id", index=True, nullable=False)
    ref: str = Field(nullable=False)
    type: FieldType = Field(nullable=False)
    title: str = Field(nullable=False)
    required: bool = Field(default=False, nullable=False)
    config: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    order: int = Field(nullable=False)

    # Relationships
    version: FormVersion = Relationship(back_populates="fields")
    choices: list["FormFieldChoice"] = Relationship(back_populates="field")


class FormFieldChoice(SQLModel, table=True):
    """Form field choice model for multiple choice options."""

    __tablename__ = "form_field_choices"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    field_id: UUID = Field(foreign_key="form_fields.id", index=True, nullable=False)
    choice_id: str = Field(nullable=False)
    label: str = Field(nullable=False)
    order: int = Field(nullable=False)

    # Relationships
    field: FormField = Relationship(back_populates="choices")


class Submission(SQLModel, table=True):
    """Submission model."""

    __tablename__ = "submissions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    form_id: UUID = Field(foreign_key="forms.id", index=True, nullable=False)
    form_version_id: UUID = Field(
        foreign_key="form_versions.id", index=True, nullable=False
    )
    workspace_id: UUID = Field(
        foreign_key="workspaces.id", index=True, nullable=False
    )  # Denormalized for RLS
    ip_address: str | None = Field(default=None, nullable=True)
    user_agent: str | None = Field(default=None, nullable=True)
    source: str | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    form: Form = Relationship(back_populates="submissions")
    form_version: FormVersion = Relationship(back_populates="submissions")
    workspace: Workspace = Relationship()
    answers: list["Answer"] = Relationship(back_populates="submission")


class Answer(SQLModel, table=True):
    """Answer model with rich value storage."""

    __tablename__ = "answers"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    submission_id: UUID = Field(
        foreign_key="submissions.id", index=True, nullable=False
    )
    field_ref: str = Field(nullable=False)
    field_type: FieldType = Field(nullable=False)
    value_jsonb: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    value_text: str | None = Field(default=None, nullable=True)
    value_number: float | None = Field(default=None, nullable=True)
    value_bool: bool | None = Field(default=None, nullable=True)
    value_time: datetime | None = Field(default=None, nullable=True)
    choice_ids: list[str] | None = Field(
        default=None, sa_column=Column(ARRAY(Text), nullable=True)
    )

    # Relationships
    submission: Submission = Relationship(back_populates="answers")
