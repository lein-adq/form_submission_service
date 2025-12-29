"""E2E tests for workspace API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestWorkspaceCRUD:
    """Test workspace CRUD endpoints."""

    def test_create_workspace(self, client: TestClient, test_user: dict):
        """Test creating a workspace."""
        response = client.post(
            "/api/v1/workspaces",
            headers=test_user["token_header"],
            json={"name": "My New Workspace"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My New Workspace"
        assert "id" in data

    def test_list_workspaces(
        self, client: TestClient, test_user: dict, test_workspace: dict
    ):
        """Test listing user's workspaces."""
        response = client.get(
            "/api/v1/workspaces",
            headers=test_user["token_header"],
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(w["id"] == str(test_workspace["id"]) for w in data)

    def test_get_workspace(
        self, client: TestClient, test_user: dict, test_workspace: dict
    ):
        """Test getting workspace details."""
        response = client.get(
            f"/api/v1/workspaces/{test_workspace['id']}",
            headers={
                **test_user["token_header"],
                "X-Workspace-ID": str(test_workspace["id"]),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == test_workspace["name"]

    def test_update_workspace(
        self, client: TestClient, test_user: dict, test_workspace: dict
    ):
        """Test updating workspace."""
        response = client.patch(
            f"/api/v1/workspaces/{test_workspace['id']}",
            headers=test_user["token_header"],
            json={"name": "Updated Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    def test_delete_workspace(
        self, client: TestClient, test_user: dict, test_workspace: dict
    ):
        """Test deleting workspace."""
        response = client.delete(
            f"/api/v1/workspaces/{test_workspace['id']}",
            headers={
                **test_user["token_header"],
                "X-Workspace-ID": str(test_workspace["id"]),
            },
        )

        assert response.status_code == 204


class TestWorkspaceMembers:
    """Test workspace membership endpoints."""

    def test_list_members(
        self, client: TestClient, test_user: dict, test_workspace: dict
    ):
        """Test listing workspace members."""
        response = client.get(
            f"/api/v1/workspaces/{test_workspace['id']}/members",
            headers=test_user["token_header"],
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(
            m["user_id"] == str(test_user["id"]) and m["role"] == "owner" for m in data
        )

    def test_add_member(
        self,
        client: TestClient,
        test_user: dict,
        test_user2: dict,
        test_workspace: dict,
    ):
        """Test adding a member to workspace."""
        response = client.post(
            f"/api/v1/workspaces/{test_workspace['id']}/members",
            headers=test_user["token_header"],
            json={
                "user_id": str(test_user2["id"]),
                "role": "viewer",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == str(test_user2["id"])
        assert data["role"] == "viewer"

    def test_update_member_role(
        self,
        client: TestClient,
        test_user: dict,
        test_user2: dict,
        test_workspace: dict,
        db_session,
    ):
        """Test updating member role."""
        from tests.fixtures.factories import create_workspace_member

        # Add user2 as member first
        create_workspace_member(
            db_session, test_workspace["id"], test_user2["id"], "viewer"
        )

        response = client.patch(
            f"/api/v1/workspaces/{test_workspace['id']}/members/{test_user2['id']}",
            headers=test_user["token_header"],
            json={"role": "admin"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"

    def test_remove_member(
        self,
        client: TestClient,
        test_user: dict,
        test_user2: dict,
        test_workspace: dict,
        db_session,
    ):
        """Test removing a member from workspace."""
        from tests.fixtures.factories import create_workspace_member

        # Add user2 as member first
        create_workspace_member(
            db_session, test_workspace["id"], test_user2["id"], "viewer"
        )

        response = client.delete(
            f"/api/v1/workspaces/{test_workspace['id']}/members/{test_user2['id']}",
            headers=test_user["token_header"],
        )

        assert response.status_code == 204


class TestWorkspaceFolders:
    """Test workspace folder endpoints."""

    def test_create_folder(
        self, client: TestClient, test_user: dict, test_workspace: dict
    ):
        """Test creating a folder."""
        response = client.post(
            f"/api/v1/workspaces/{test_workspace['id']}/folders",
            headers=test_user["token_header"],
            json={"name": "My Folder", "parent_id": None},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Folder"
        assert data["workspace_id"] == str(test_workspace["id"])

    def test_list_folders(
        self, client: TestClient, test_user: dict, test_workspace: dict, db_session
    ):
        """Test listing folders in workspace."""
        from tests.fixtures.factories import create_folder

        folder = create_folder(db_session, test_workspace["id"], "Test Folder")

        response = client.get(
            f"/api/v1/workspaces/{test_workspace['id']}/folders",
            headers=test_user["token_header"],
        )

        assert response.status_code == 200
        data = response.json()
        assert any(f["id"] == str(folder.id) for f in data)

    def test_update_folder(
        self, client: TestClient, test_user: dict, test_workspace: dict, db_session
    ):
        """Test updating a folder."""
        from tests.fixtures.factories import create_folder

        folder = create_folder(db_session, test_workspace["id"], "Old Name")

        response = client.patch(
            f"/api/v1/workspaces/folders/{folder.id}",
            headers=test_user["token_header"],
            json={"name": "New Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"

    def test_delete_folder(
        self, client: TestClient, test_user: dict, test_workspace: dict, db_session
    ):
        """Test deleting a folder."""
        from tests.fixtures.factories import create_folder

        folder = create_folder(db_session, test_workspace["id"], "Test Folder")

        response = client.delete(
            f"/api/v1/workspaces/folders/{folder.id}",
            headers=test_user["token_header"],
        )

        assert response.status_code == 204
