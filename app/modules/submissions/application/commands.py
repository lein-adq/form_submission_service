"""Submissions application commands."""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class CreateSubmissionCommand:
    """Command to create a submission."""

    form_id: UUID
    answers: list[dict[str, str | None]]
    ip_address: str | None = None
    user_agent: str | None = None
    source: str | None = None
