"""Workspaces domain repository interfaces."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.domain.permissions import Role
from app.modules.workspaces.domain.entities import Folder, Membership, Workspace


class WorkspaceRepository(ABC):
    """Repository interface for workspace operations."""

    @abstractmethod
    def create(self, workspace: Workspace) -> Workspace:
        """Create a new workspace."""
        pass

    @abstractmethod
    def get_by_id(self, workspace_id: UUID) -> Workspace | None:
        """Get workspace by ID."""
        pass

    @abstractmethod
    def list_by_user(self, user_id: UUID) -> list[Workspace]:
        """List workspaces for a user."""
        pass

    @abstractmethod
    def update(self, workspace: Workspace) -> Workspace:
        """Update a workspace."""
        pass

    @abstractmethod
    def delete(self, workspace_id: UUID) -> None:
        """Delete a workspace."""
        pass


class MembershipRepository(ABC):
    """Repository interface for membership operations."""

    @abstractmethod
    def create(self, membership: Membership) -> Membership:
        """Create a new membership."""
        pass

    @abstractmethod
    def get(self, workspace_id: UUID, user_id: UUID) -> Membership | None:
        """Get membership by workspace and user."""
        pass

    @abstractmethod
    def list_by_workspace(self, workspace_id: UUID) -> list[Membership]:
        """List memberships for a workspace."""
        pass

    @abstractmethod
    def list_by_user(self, user_id: UUID) -> list[Membership]:
        """List memberships for a user."""
        pass

    @abstractmethod
    def update_role(self, workspace_id: UUID, user_id: UUID, role: Role) -> Membership:
        """Update membership role."""
        pass

    @abstractmethod
    def delete(self, workspace_id: UUID, user_id: UUID) -> None:
        """Delete a membership."""
        pass


class FolderRepository(ABC):
    """Repository interface for folder operations."""

    @abstractmethod
    def create(self, folder: Folder) -> Folder:
        """Create a new folder."""
        pass

    @abstractmethod
    def get_by_id(self, folder_id: UUID) -> Folder | None:
        """Get folder by ID."""
        pass

    @abstractmethod
    def list_by_workspace(self, workspace_id: UUID) -> list[Folder]:
        """List root folders for a workspace."""
        pass

    @abstractmethod
    def list_children(self, parent_id: UUID) -> list[Folder]:
        """List child folders."""
        pass

    @abstractmethod
    def update(self, folder: Folder) -> Folder:
        """Update a folder."""
        pass

    @abstractmethod
    def delete(self, folder_id: UUID) -> None:
        """Delete a folder."""
        pass

    @abstractmethod
    def move(self, folder_id: UUID, new_parent_id: UUID | None) -> Folder:
        """Move folder to a new parent."""
        pass
