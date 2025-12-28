"""Forms API schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.core.domain.value_objects import FieldType, FormStatus, VersionState


class FormCreate(BaseModel):
    """Request schema for creating a form."""

    name: str


class FormUpdate(BaseModel):
    """Request schema for updating a form."""

    name: str


class FormDefinitionUpdate(BaseModel):
    """Request schema for updating form definition."""

    definition: dict[str, Any]


class FormMoveRequest(BaseModel):
    """Request schema for moving form to folder."""

    folder_id: UUID | None = None


class FormDuplicateRequest(BaseModel):
    """Request schema for duplicating a form."""

    new_name: str


class FormResponse(BaseModel):
    """Response schema for form."""

    id: UUID
    workspace_id: UUID
    folder_id: UUID | None = None
    name: str
    status: FormStatus
    draft_version_id: UUID | None = None
    published_version_id: UUID | None = None
    created_by: UUID | None
    created_at: datetime

    class Config:
        from_attributes = True


class FormVersionResponse(BaseModel):
    """Response schema for form version."""

    id: UUID
    form_id: UUID
    version_number: int
    state: VersionState
    definition_jsonb: dict[str, Any]
    created_by: UUID | None
    created_at: datetime

    class Config:
        from_attributes = True


class FormFieldResponse(BaseModel):
    """Response schema for form field."""

    id: UUID
    version_id: UUID
    ref: str
    type: FieldType
    title: str
    required: bool
    config: dict[str, Any] | None = None
    order: int

    class Config:
        from_attributes = True


class FormFieldChoiceResponse(BaseModel):
    """Response schema for form field choice."""

    id: UUID
    field_id: UUID
    choice_id: str
    label: str
    order: int

    class Config:
        from_attributes = True
