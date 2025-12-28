"""Submissions domain policies and business rules."""

from app.core.domain.value_objects import FormStatus
from app.modules.forms.domain.entities import Form


def can_accept_submission(form: Form) -> bool:
    """Check if form can accept submissions."""
    return form.status == FormStatus.PUBLISHED


def is_submission_immutable() -> bool:
    """Submissions are immutable after creation."""
    return True
