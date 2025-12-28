"""Workspaces application commands."""

from dataclasses import dataclass
from uuid import UUID

from app.core.domain.permissions import Role


@dataclass
class CreateWorkspaceCommand:
    """Command to create a workspace."""

    name: str
    creator_user_id: UUID


@dataclass
class UpdateWorkspaceCommand:
    """Command to update a workspace."""

    workspace_id: UUID
    name: str


@dataclass
class DeleteWorkspaceCommand:
    """Command to delete a workspace."""

    workspace_id: UUID


@dataclass
class AddMemberCommand:
    """Command to add a member to a workspace."""

    workspace_id: UUID
    user_id: UUID
    role: Role


@dataclass
class UpdateMemberRoleCommand:
    """Command to update a member's role."""

    workspace_id: UUID
    user_id: UUID
    role: Role


@dataclass
class RemoveMemberCommand:
    """Command to remove a member from a workspace."""

    workspace_id: UUID
    user_id: UUID


@dataclass
class CreateFolderCommand:
    """Command to create a folder."""

    workspace_id: UUID
    name: str
    parent_id: UUID | None = None


@dataclass
class UpdateFolderCommand:
    """Command to update a folder."""

    folder_id: UUID
    name: str


@dataclass
class MoveFolderCommand:
    """Command to move a folder to a new parent."""

    folder_id: UUID
    new_parent_id: UUID | None = None


@dataclass
class DeleteFolderCommand:
    """Command to delete a folder."""

    folder_id: UUID
