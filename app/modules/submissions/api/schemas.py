"""Submissions API schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.core.domain.value_objects import FieldType


class SubmissionCreate(BaseModel):
    """Request schema for creating a submission."""

    answers: dict[str, str | None]
    ip_address: str | None = None
    user_agent: str | None = None
    source: str | None = None


class AnswerResponse(BaseModel):
    """Response schema for answer."""

    id: UUID
    submission_id: UUID
    field_ref: str
    field_type: FieldType
    value_jsonb: dict[str, Any] | None = None
    value_text: str | None = None
    value_number: float | None = None
    value_bool: bool | None = None
    value_time: datetime | None = None
    choice_ids: list[str] | None = None

    class Config:
        from_attributes = True


class SubmissionResponse(BaseModel):
    """Response schema for submission."""

    id: UUID
    form_id: UUID
    form_version_id: UUID
    workspace_id: UUID
    ip_address: str | None = None
    user_agent: str | None = None
    source: str | None = None
    created_at: datetime
    answers: list[AnswerResponse] = []

    class Config:
        from_attributes = True
