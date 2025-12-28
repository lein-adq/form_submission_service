"""PostgreSQL implementation of workspace repositories."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.db.models import Folder as FolderModel
from app.core.db.models import Workspace as WorkspaceModel
from app.core.db.models import WorkspaceMember as WorkspaceMemberModel
from app.core.domain.permissions import Role
from app.modules.workspaces.domain.entities import Folder, Membership, Workspace
from app.modules.workspaces.domain.repositories import (
    FolderRepository,
    MembershipRepository,
    WorkspaceRepository,
)


def _workspace_model_to_entity(db_workspace: WorkspaceModel) -> Workspace:
    """Convert Workspace model to domain entity."""
    return Workspace(
        id=db_workspace.id,
        name=db_workspace.name,
        created_at=db_workspace.created_at,
    )


def _membership_model_to_entity(db_membership: WorkspaceMemberModel) -> Membership:
    """Convert WorkspaceMember model to domain entity."""
    return Membership(
        workspace_id=db_membership.workspace_id,
        user_id=db_membership.user_id,
        role=db_membership.role,
        created_at=db_membership.created_at,
    )


def _folder_model_to_entity(db_folder: FolderModel) -> Folder:
    """Convert Folder model to domain entity."""
    return Folder(
        id=db_folder.id,
        workspace_id=db_folder.workspace_id,
        name=db_folder.name,
        parent_id=db_folder.parent_id,
        created_at=db_folder.created_at,
    )


class PostgreSQLWorkspaceRepository(WorkspaceRepository):
    """PostgreSQL implementation of WorkspaceRepository."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, workspace: Workspace) -> Workspace:
        """Create a new workspace."""
        db_workspace = WorkspaceModel(name=workspace.name)
        self.db.add(db_workspace)
        self.db.commit()
        self.db.refresh(db_workspace)
        return _workspace_model_to_entity(db_workspace)

    def get_by_id(self, workspace_id: UUID) -> Workspace | None:
        """Get workspace by ID."""
        db_workspace = (
            self.db.query(WorkspaceModel)
            .filter(WorkspaceModel.id == workspace_id)
            .first()
        )
        if not db_workspace:
            return None
        return _workspace_model_to_entity(db_workspace)

    def list_by_user(self, user_id: UUID) -> list[Workspace]:
        """List workspaces for a user."""
        db_workspaces = (
            self.db.query(WorkspaceModel)
            .join(WorkspaceMemberModel)
            .filter(WorkspaceMemberModel.user_id == user_id)
            .all()
        )
        return [_workspace_model_to_entity(w) for w in db_workspaces]

    def update(self, workspace: Workspace) -> Workspace:
        """Update a workspace."""
        db_workspace = (
            self.db.query(WorkspaceModel)
            .filter(WorkspaceModel.id == workspace.id)
            .first()
        )
        if not db_workspace:
            raise ValueError("Workspace not found")
        db_workspace.name = workspace.name
        self.db.commit()
        self.db.refresh(db_workspace)
        return _workspace_model_to_entity(db_workspace)

    def delete(self, workspace_id: UUID) -> None:
        """Delete a workspace."""
        db_workspace = (
            self.db.query(WorkspaceModel)
            .filter(WorkspaceModel.id == workspace_id)
            .first()
        )
        if db_workspace:
            self.db.delete(db_workspace)
            self.db.commit()


class PostgreSQLMembershipRepository(MembershipRepository):
    """PostgreSQL implementation of MembershipRepository."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, membership: Membership) -> Membership:
        """Create a new membership."""
        db_membership = WorkspaceMemberModel(
            workspace_id=membership.workspace_id,
            user_id=membership.user_id,
            role=membership.role,
        )
        self.db.add(db_membership)
        self.db.commit()
        self.db.refresh(db_membership)
        return _membership_model_to_entity(db_membership)

    def get(self, workspace_id: UUID, user_id: UUID) -> Membership | None:
        """Get membership by workspace and user."""
        db_membership = (
            self.db.query(WorkspaceMemberModel)
            .filter(
                WorkspaceMemberModel.workspace_id == workspace_id,
                WorkspaceMemberModel.user_id == user_id,
            )
            .first()
        )
        if not db_membership:
            return None
        return _membership_model_to_entity(db_membership)

    def list_by_workspace(self, workspace_id: UUID) -> list[Membership]:
        """List memberships for a workspace."""
        db_memberships = (
            self.db.query(WorkspaceMemberModel)
            .filter(WorkspaceMemberModel.workspace_id == workspace_id)
            .all()
        )
        return [_membership_model_to_entity(m) for m in db_memberships]

    def list_by_user(self, user_id: UUID) -> list[Membership]:
        """List memberships for a user."""
        db_memberships = (
            self.db.query(WorkspaceMemberModel)
            .filter(WorkspaceMemberModel.user_id == user_id)
            .all()
        )
        return [_membership_model_to_entity(m) for m in db_memberships]

    def update_role(self, workspace_id: UUID, user_id: UUID, role: Role) -> Membership:
        """Update membership role."""
        db_membership = (
            self.db.query(WorkspaceMemberModel)
            .filter(
                WorkspaceMemberModel.workspace_id == workspace_id,
                WorkspaceMemberModel.user_id == user_id,
            )
            .first()
        )
        if not db_membership:
            raise ValueError("Membership not found")
        db_membership.role = role
        self.db.commit()
        self.db.refresh(db_membership)
        return _membership_model_to_entity(db_membership)

    def delete(self, workspace_id: UUID, user_id: UUID) -> None:
        """Delete a membership."""
        db_membership = (
            self.db.query(WorkspaceMemberModel)
            .filter(
                WorkspaceMemberModel.workspace_id == workspace_id,
                WorkspaceMemberModel.user_id == user_id,
            )
            .first()
        )
        if not db_membership:
            raise ValueError("Membership not found")
        self.db.delete(db_membership)
        self.db.commit()


class PostgreSQLFolderRepository(FolderRepository):
    """PostgreSQL implementation of FolderRepository."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, folder: Folder) -> Folder:
        """Create a new folder."""
        db_folder = FolderModel(
            workspace_id=folder.workspace_id,
            name=folder.name,
            parent_id=folder.parent_id,
        )
        self.db.add(db_folder)
        self.db.commit()
        self.db.refresh(db_folder)
        return _folder_model_to_entity(db_folder)

    def get_by_id(self, folder_id: UUID) -> Folder | None:
        """Get folder by ID."""
        db_folder = (
            self.db.query(FolderModel).filter(FolderModel.id == folder_id).first()
        )
        if not db_folder:
            return None
        return _folder_model_to_entity(db_folder)

    def list_by_workspace(self, workspace_id: UUID) -> list[Folder]:
        """List root folders for a workspace."""
        db_folders = (
            self.db.query(FolderModel)
            .filter(
                FolderModel.workspace_id == workspace_id,
                FolderModel.parent_id.is_(None),
            )
            .all()
        )
        return [_folder_model_to_entity(f) for f in db_folders]

    def list_children(self, parent_id: UUID) -> list[Folder]:
        """List child folders."""
        db_folders = (
            self.db.query(FolderModel).filter(FolderModel.parent_id == parent_id).all()
        )
        return [_folder_model_to_entity(f) for f in db_folders]

    def update(self, folder: Folder) -> Folder:
        """Update a folder."""
        db_folder = (
            self.db.query(FolderModel).filter(FolderModel.id == folder.id).first()
        )
        if not db_folder:
            raise ValueError("Folder not found")
        db_folder.name = folder.name
        self.db.commit()
        self.db.refresh(db_folder)
        return _folder_model_to_entity(db_folder)

    def delete(self, folder_id: UUID) -> None:
        """Delete a folder."""
        db_folder = (
            self.db.query(FolderModel).filter(FolderModel.id == folder_id).first()
        )
        if not db_folder:
            raise ValueError("Folder not found")
        self.db.delete(db_folder)
        self.db.commit()

    def move(self, folder_id: UUID, new_parent_id: UUID | None) -> Folder:
        """Move folder to a new parent."""
        db_folder = (
            self.db.query(FolderModel).filter(FolderModel.id == folder_id).first()
        )
        if not db_folder:
            raise ValueError("Folder not found")
        db_folder.parent_id = new_parent_id
        self.db.commit()
        self.db.refresh(db_folder)
        return _folder_model_to_entity(db_folder)
