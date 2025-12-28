"""Workspaces domain policies and business rules."""

from app.core.domain.permissions import Role
from app.modules.workspaces.domain.repositories import MembershipRepository


def ensure_workspace_has_owner(
    membership_repository: MembershipRepository,
    workspace_id: str,
    exclude_user_id: str | None = None,
) -> None:
    """Ensure workspace has at least one owner (before removing a member)."""
    memberships = membership_repository.list_by_workspace(workspace_id)
    owners = [m for m in memberships if m.role == Role.OWNER]
    if exclude_user_id:
        owners = [o for o in owners if str(o.user_id) != exclude_user_id]
    if not owners:
        raise ValueError("Workspace must have at least one owner")
