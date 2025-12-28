"""Forms domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from app.core.domain.value_objects import FieldType, FormStatus, VersionState


@dataclass
class FormFieldChoice:
    """Form field choice domain entity."""

    id: UUID
    field_id: UUID
    choice_id: str
    label: str
    order: int


@dataclass
class FormField:
    """Form field domain entity."""

    id: UUID
    version_id: UUID
    ref: str
    type: FieldType
    title: str
    order: int
    required: bool = False
    config: dict[str, Any] | None = None
    choices: list[FormFieldChoice] = field(default_factory=list)


@dataclass
class FormVersion:
    """Form version domain entity."""

    id: UUID
    form_id: UUID
    version_number: int
    state: VersionState
    definition_jsonb: dict[str, Any]
    created_by: UUID | None = None
    created_at: datetime | None = None
    fields: list[FormField] = field(default_factory=list)


@dataclass
class Form:
    """Form domain entity."""

    id: UUID
    workspace_id: UUID
    name: str
    status: FormStatus
    folder_id: UUID | None = None
    draft_version_id: UUID | None = None
    published_version_id: UUID | None = None
    created_by: UUID | None = None
    created_at: datetime | None = None
    versions: list[FormVersion] = field(default_factory=list)
