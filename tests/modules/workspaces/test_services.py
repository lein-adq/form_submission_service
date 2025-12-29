"""Unit tests for workspace services."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

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
from app.modules.workspaces.application.services import (
    FolderService,
    MembershipService,
    WorkspaceService,
)
from app.modules.workspaces.domain.entities import Folder, Membership, Workspace


class TestWorkspaceService:
    """Test WorkspaceService business logic."""

    def test_create_workspace(self):
        """Test creating a workspace."""
        mock_workspace_repo = Mock()
        mock_membership_repo = Mock()

        workspace_id = uuid4()
        workspace = Workspace(id=workspace_id, name="Test Workspace")
        mock_workspace_repo.create.return_value = workspace

        membership = Membership(
            workspace_id=workspace_id,
            user_id=uuid4(),
            role="owner",
        )
        mock_membership_repo.create.return_value = membership

        service = WorkspaceService(mock_workspace_repo, mock_membership_repo)
        command = CreateWorkspaceCommand(
            name="Test Workspace",
            creator_user_id=uuid4(),
        )

        result = service.create(command)

        assert result.name == "Test Workspace"
        mock_workspace_repo.create.assert_called_once()
        mock_membership_repo.create.assert_called_once()

    def test_update_workspace(self):
        """Test updating a workspace."""
        mock_workspace_repo = Mock()
        mock_membership_repo = Mock()

        workspace_id = uuid4()
        workspace = Workspace(id=workspace_id, name="Old Name")
        mock_workspace_repo.get_by_id.return_value = workspace

        # Mock update to return workspace with updated name
        updated_workspace = Workspace(id=workspace_id, name="New Name")
        mock_workspace_repo.update.return_value = updated_workspace

        service = WorkspaceService(mock_workspace_repo, mock_membership_repo)
        command = UpdateWorkspaceCommand(
            workspace_id=workspace_id,
            name="New Name",
        )

        result = service.update(command)

        assert result.name == "New Name"
        mock_workspace_repo.update.assert_called_once()

    def test_update_workspace_not_found(self):
        """Test updating non-existent workspace."""
        mock_workspace_repo = Mock()
        mock_membership_repo = Mock()
        mock_workspace_repo.get_by_id.return_value = None

        service = WorkspaceService(mock_workspace_repo, mock_membership_repo)
        command = UpdateWorkspaceCommand(
            workspace_id=uuid4(),
            name="New Name",
        )

        with pytest.raises(NotFoundError):
            service.update(command)

    def test_delete_workspace(self):
        """Test deleting a workspace."""
        mock_workspace_repo = Mock()
        mock_membership_repo = Mock()

        workspace_id = uuid4()
        workspace = Workspace(id=workspace_id, name="Test Workspace")
        mock_workspace_repo.get_by_id.return_value = workspace

        service = WorkspaceService(mock_workspace_repo, mock_membership_repo)
        command = DeleteWorkspaceCommand(workspace_id=workspace_id)

        service.delete(command)

        mock_workspace_repo.delete.assert_called_once_with(workspace_id)


class TestMembershipService:
    """Test MembershipService business logic."""

    def test_add_member(self):
        """Test adding a member to workspace."""
        mock_workspace_repo = Mock()
        mock_membership_repo = Mock()

        workspace_id = uuid4()
        user_id = uuid4()

        workspace = Workspace(id=workspace_id, name="Test Workspace")
        mock_workspace_repo.get_by_id.return_value = workspace

        # Service uses get() method, not get_by_workspace_and_user
        mock_membership_repo.get.return_value = None

        membership = Membership(
            workspace_id=workspace_id,
            user_id=user_id,
            role="viewer",
        )
        mock_membership_repo.create.return_value = membership

        service = MembershipService(mock_workspace_repo, mock_membership_repo)
        command = AddMemberCommand(
            workspace_id=workspace_id,
            user_id=user_id,
            role="viewer",
        )

        result = service.add_member(command)

        assert result.user_id == user_id
        assert result.role == "viewer"
        mock_membership_repo.create.assert_called_once()

    def test_add_member_already_exists(self):
        """Test adding member who is already in workspace."""
        mock_workspace_repo = Mock()
        mock_membership_repo = Mock()

        workspace_id = uuid4()
        user_id = uuid4()

        workspace = Workspace(id=workspace_id, name="Test Workspace")
        mock_workspace_repo.get_by_id.return_value = workspace

        existing_membership = Membership(
            workspace_id=workspace_id,
            user_id=user_id,
            role="viewer",
        )
        mock_membership_repo.get.return_value = existing_membership

        service = MembershipService(mock_workspace_repo, mock_membership_repo)
        command = AddMemberCommand(
            workspace_id=workspace_id,
            user_id=user_id,
            role="member",
        )

        with pytest.raises(ConflictError):
            service.add_member(command)

    def test_update_member_role(self):
        """Test updating member role."""
        mock_workspace_repo = Mock()
        mock_membership_repo = Mock()

        workspace_id = uuid4()
        user_id = uuid4()

        membership = Membership(
            workspace_id=workspace_id,
            user_id=user_id,
            role="viewer",
        )
        mock_membership_repo.get.return_value = membership

        # Mock update_role to return membership with updated role
        updated_membership = Membership(
            workspace_id=workspace_id,
            user_id=user_id,
            role="admin",
        )
        mock_membership_repo.update_role.return_value = updated_membership

        service = MembershipService(mock_workspace_repo, mock_membership_repo)
        command = UpdateMemberRoleCommand(
            workspace_id=workspace_id,
            user_id=user_id,
            role="admin",
        )

        result = service.update_role(command)

        assert result.role == "admin"
        mock_membership_repo.update_role.assert_called_once()

    def test_remove_member(self):
        """Test removing a member from workspace."""
        mock_workspace_repo = Mock()
        mock_membership_repo = Mock()

        workspace_id = uuid4()
        user_id = uuid4()

        membership = Membership(
            workspace_id=workspace_id,
            user_id=user_id,
            role="member",
        )
        mock_membership_repo.get_by_workspace_and_user.return_value = membership

        service = MembershipService(mock_workspace_repo, mock_membership_repo)
        command = RemoveMemberCommand(
            workspace_id=workspace_id,
            user_id=user_id,
        )

        service.remove_member(command)

        mock_membership_repo.delete.assert_called_once()


class TestFolderService:
    """Test FolderService business logic."""

    def test_create_folder(self):
        """Test creating a folder."""
        mock_folder_repo = Mock()
        mock_workspace_repo = Mock()

        workspace_id = uuid4()
        workspace = Workspace(id=workspace_id, name="Test Workspace")
        mock_workspace_repo.get_by_id.return_value = workspace

        folder = Folder(
            id=uuid4(),
            workspace_id=workspace_id,
            name="Test Folder",
            parent_id=None,
        )
        mock_folder_repo.create.return_value = folder

        service = FolderService(mock_folder_repo, mock_workspace_repo)
        command = CreateFolderCommand(
            workspace_id=workspace_id,
            name="Test Folder",
            parent_id=None,
        )

        result = service.create(command)

        assert result.name == "Test Folder"
        mock_folder_repo.create.assert_called_once()

    def test_update_folder(self):
        """Test updating a folder."""
        mock_folder_repo = Mock()
        mock_workspace_repo = Mock()

        folder_id = uuid4()
        folder = Folder(
            id=folder_id,
            workspace_id=uuid4(),
            name="Old Name",
            parent_id=None,
        )
        mock_folder_repo.get_by_id.return_value = folder

        # Mock update to return folder with updated name
        updated_folder = Folder(
            id=folder_id,
            workspace_id=folder.workspace_id,
            name="New Name",
            parent_id=folder.parent_id,
        )
        mock_folder_repo.update.return_value = updated_folder

        service = FolderService(mock_folder_repo, mock_workspace_repo)
        command = UpdateFolderCommand(
            folder_id=folder_id,
            name="New Name",
        )

        result = service.update(command)

        assert result.name == "New Name"
        mock_folder_repo.update.assert_called_once()

    def test_move_folder(self):
        """Test moving a folder to new parent."""
        mock_folder_repo = Mock()
        mock_workspace_repo = Mock()

        folder_id = uuid4()
        new_parent_id = uuid4()

        folder = Folder(
            id=folder_id,
            workspace_id=uuid4(),
            name="Test Folder",
            parent_id=None,
        )
        parent_folder = Folder(
            id=new_parent_id,
            workspace_id=folder.workspace_id,
            name="Parent Folder",
            parent_id=None,
        )

        # Service calls get_by_id multiple times:
        # 1. Get folder to move
        # 2. Get new_parent (for loop check)
        # 3. Get new_parent again (to verify it exists)
        # Then calls move() which returns updated folder
        updated_folder = Folder(
            id=folder_id,
            workspace_id=folder.workspace_id,
            name=folder.name,
            parent_id=new_parent_id,
        )
        mock_folder_repo.get_by_id.side_effect = [folder, parent_folder, parent_folder]
        mock_folder_repo.move.return_value = updated_folder

        service = FolderService(mock_folder_repo, mock_workspace_repo)
        command = MoveFolderCommand(
            folder_id=folder_id,
            new_parent_id=new_parent_id,
        )

        result = service.move(command)

        assert result.parent_id == new_parent_id
        mock_folder_repo.move.assert_called_once()

    def test_delete_folder(self):
        """Test deleting a folder."""
        mock_folder_repo = Mock()
        mock_workspace_repo = Mock()

        folder_id = uuid4()
        folder = Folder(
            id=folder_id,
            workspace_id=uuid4(),
            name="Test Folder",
            parent_id=None,
        )
        mock_folder_repo.get_by_id.return_value = folder
        mock_folder_repo.list_children.return_value = []  # No children

        service = FolderService(mock_folder_repo, mock_workspace_repo)
        command = DeleteFolderCommand(folder_id=folder_id)

        service.delete(command)

        mock_folder_repo.delete.assert_called_once_with(folder_id)

    def test_delete_folder_with_children(self):
        """Test deleting folder with children raises error."""
        mock_folder_repo = Mock()
        mock_workspace_repo = Mock()

        folder_id = uuid4()
        folder = Folder(
            id=folder_id,
            workspace_id=uuid4(),
            name="Test Folder",
            parent_id=None,
        )
        child_folder = Folder(
            id=uuid4(),
            workspace_id=folder.workspace_id,
            name="Child Folder",
            parent_id=folder_id,
        )

        mock_folder_repo.get_by_id.return_value = folder
        mock_folder_repo.list_children.return_value = [child_folder]

        service = FolderService(mock_folder_repo, mock_workspace_repo)
        command = DeleteFolderCommand(folder_id=folder_id)

        with pytest.raises(ConflictError):
            service.delete(command)
