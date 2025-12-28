"""Submissions domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from app.core.domain.value_objects import FieldType


@dataclass
class Answer:
    """Answer domain entity with rich value storage."""

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


@dataclass
class Submission:
    """Submission domain entity."""

    id: UUID
    form_id: UUID
    form_version_id: UUID
    workspace_id: UUID
    ip_address: str | None = None
    user_agent: str | None = None
    source: str | None = None
    created_at: datetime | None = None
    answers: list[Answer] = field(default_factory=list)
