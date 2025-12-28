"""Workspaces application services."""

from uuid import UUID

from app.core.domain.permissions import Role
from app.core.exceptions import ConflictError, NotFoundError
from app.modules.workspaces.application.commands import (
    AddMemberCommand,
    CreateFolderCommand,
    CreateWorkspaceCommand,
    DeleteFolderCommand,
    DeleteWorkspaceCommand,
    MoveFolderCommand,
    RemoveMemberCommand,
    UpdateFolderCommand,
    UpdateMemberRoleCommand,
    UpdateWorkspaceCommand,
)
from app.modules.workspaces.domain.entities import Membership, Workspace
from app.modules.workspaces.domain.policies import ensure_workspace_has_owner
from app.modules.workspaces.domain.entities import Folder
from app.modules.workspaces.domain.repositories import (
    FolderRepository,
    MembershipRepository,
    WorkspaceRepository,
)


class WorkspaceService:
    """Service for workspace operations."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        membership_repository: MembershipRepository,
    ) -> None:
        self.workspace_repository = workspace_repository
        self.membership_repository = membership_repository

    def create(self, command: CreateWorkspaceCommand) -> Workspace:
        """Create a new workspace and add creator as owner."""
        workspace = Workspace(
            id=UUID(int=0),  # Will be set by repository
            name=command.name,
        )
        created_workspace = self.workspace_repository.create(workspace)

        # Add creator as owner
        membership = Membership(
            workspace_id=created_workspace.id,
            user_id=command.creator_user_id,
            role=Role.OWNER,
        )
        self.membership_repository.create(membership)

        return created_workspace

    def get_by_id(self, workspace_id: UUID) -> Workspace:
        """Get workspace by ID."""
        workspace = self.workspace_repository.get_by_id(workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")
        return workspace

    def list_by_user(self, user_id: UUID) -> list[Workspace]:
        """List workspaces for a user."""
        return self.workspace_repository.list_by_user(user_id)

    def update(self, command: UpdateWorkspaceCommand) -> Workspace:
        """Update a workspace."""
        workspace = self.workspace_repository.get_by_id(command.workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")

        updated_workspace = Workspace(
            id=workspace.id,
            name=command.name,
        )
        return self.workspace_repository.update(updated_workspace)

    def delete(self, command: DeleteWorkspaceCommand) -> None:
        """Delete a workspace."""
        workspace = self.workspace_repository.get_by_id(command.workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")

        self.workspace_repository.delete(command.workspace_id)


class MembershipService:
    """Service for membership operations."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        membership_repository: MembershipRepository,
    ) -> None:
        self.workspace_repository = workspace_repository
        self.membership_repository = membership_repository

    def add_member(self, command: AddMemberCommand) -> Membership:
        """Add a member to a workspace."""
        # Verify workspace exists
        workspace = self.workspace_repository.get_by_id(command.workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")

        # Check if membership already exists
        existing = self.membership_repository.get(command.workspace_id, command.user_id)
        if existing:
            raise ConflictError("User is already a member of this workspace")

        membership = Membership(
            workspace_id=command.workspace_id,
            user_id=command.user_id,
            role=command.role,
        )
        return self.membership_repository.create(membership)

    def update_role(self, command: UpdateMemberRoleCommand) -> Membership:
        """Update a member's role."""
        membership = self.membership_repository.get(
            command.workspace_id, command.user_id
        )
        if not membership:
            raise NotFoundError("Membership not found")

        # If removing owner, ensure workspace still has at least one owner
        if membership.role == Role.OWNER and command.role != Role.OWNER:
            ensure_workspace_has_owner(
                self.membership_repository,
                str(command.workspace_id),
                exclude_user_id=str(command.user_id),
            )

        return self.membership_repository.update_role(
            command.workspace_id,
            command.user_id,
            command.role,
        )

    def remove_member(self, command: RemoveMemberCommand) -> None:
        """Remove a member from a workspace."""
        membership = self.membership_repository.get(
            command.workspace_id, command.user_id
        )
        if not membership:
            raise NotFoundError("Membership not found")

        # If removing owner, ensure workspace still has at least one owner
        if membership.role == Role.OWNER:
            ensure_workspace_has_owner(
                self.membership_repository,
                str(command.workspace_id),
                exclude_user_id=str(command.user_id),
            )

        self.membership_repository.delete(command.workspace_id, command.user_id)

    def list_by_workspace(self, workspace_id: UUID) -> list[Membership]:
        """List memberships for a workspace."""
        return self.membership_repository.list_by_workspace(workspace_id)


class FolderService:
    """Service for folder operations."""

    def __init__(
        self,
        folder_repository: FolderRepository,
        workspace_repository: WorkspaceRepository,
    ) -> None:
        self.folder_repository = folder_repository
        self.workspace_repository = workspace_repository

    def create(self, command: CreateFolderCommand) -> Folder:
        """Create a new folder."""
        # Verify workspace exists
        workspace = self.workspace_repository.get_by_id(command.workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")

        # If parent_id is provided, verify it exists and belongs to same workspace
        if command.parent_id:
            parent = self.folder_repository.get_by_id(command.parent_id)
            if not parent:
                raise NotFoundError("Parent folder not found")
            if parent.workspace_id != command.workspace_id:
                raise ConflictError("Parent folder must be in the same workspace")

        folder = Folder(
            id=UUID(int=0),  # Will be set by repository
            workspace_id=command.workspace_id,
            name=command.name,
            parent_id=command.parent_id,
        )
        return self.folder_repository.create(folder)

    def get_by_id(self, folder_id: UUID) -> Folder:
        """Get folder by ID."""
        folder = self.folder_repository.get_by_id(folder_id)
        if not folder:
            raise NotFoundError("Folder not found")
        return folder

    def list_by_workspace(self, workspace_id: UUID) -> list[Folder]:
        """List root folders for a workspace."""
        return self.folder_repository.list_by_workspace(workspace_id)

    def list_children(self, parent_id: UUID) -> list[Folder]:
        """List child folders."""
        return self.folder_repository.list_children(parent_id)

    def update(self, command: UpdateFolderCommand) -> Folder:
        """Update a folder."""
        folder = self.folder_repository.get_by_id(command.folder_id)
        if not folder:
            raise NotFoundError("Folder not found")

        updated_folder = Folder(
            id=folder.id,
            workspace_id=folder.workspace_id,
            name=command.name,
            parent_id=folder.parent_id,
        )
        return self.folder_repository.update(updated_folder)

    def move(self, command: MoveFolderCommand) -> Folder:
        """Move folder to a new parent."""
        folder = self.folder_repository.get_by_id(command.folder_id)
        if not folder:
            raise NotFoundError("Folder not found")

        # Prevent moving folder into itself or its descendants
        if command.new_parent_id:
            if command.new_parent_id == command.folder_id:
                raise ConflictError("Cannot move folder into itself")
            # Check if new parent is a descendant
            current = self.folder_repository.get_by_id(command.new_parent_id)
            while current and current.parent_id:
                if current.parent_id == command.folder_id:
                    raise ConflictError("Cannot move folder into its own descendant")
                current = self.folder_repository.get_by_id(current.parent_id)

            # Verify new parent exists and is in same workspace
            new_parent = self.folder_repository.get_by_id(command.new_parent_id)
            if not new_parent:
                raise NotFoundError("New parent folder not found")
            if new_parent.workspace_id != folder.workspace_id:
                raise ConflictError("New parent must be in the same workspace")

        return self.folder_repository.move(command.folder_id, command.new_parent_id)

    def delete(self, command: DeleteFolderCommand) -> None:
        """Delete a folder."""
        folder = self.folder_repository.get_by_id(command.folder_id)
        if not folder:
            raise NotFoundError("Folder not found")

        # Check if folder has children
        children = self.folder_repository.list_children(command.folder_id)
        if children:
            raise ConflictError("Cannot delete folder with child folders")

        self.folder_repository.delete(command.folder_id)
