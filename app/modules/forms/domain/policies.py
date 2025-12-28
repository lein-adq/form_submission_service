"""Forms domain policies and business rules."""

from app.core.domain.permissions import Role
from app.core.domain.value_objects import FormStatus
from app.modules.forms.domain.entities import Form


def can_modify_form(user_role: Role) -> bool:
    """Check if user role can modify forms."""
    return user_role in (Role.EDITOR, Role.ADMIN, Role.OWNER)


def can_delete_form(user_role: Role) -> bool:
    """Check if user role can delete forms."""
    return user_role in (Role.ADMIN, Role.OWNER)


def can_publish_form(form: Form) -> bool:
    """Check if form can be published."""
    return form.status == FormStatus.DRAFT


def can_archive_form(form: Form) -> bool:
    """Check if form can be archived."""
    return form.status in (FormStatus.DRAFT, FormStatus.PUBLISHED)
