"""E2E tests for form API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestFormCRUD:
    """Test form CRUD endpoints."""

    def test_create_form(
        self, client: TestClient, test_user: dict, test_workspace: dict
    ):
        """Test creating a form."""
        response = client.post(
            f"/api/v1/workspaces/{test_workspace['id']}/forms",
            headers={
                **test_user["token_header"],
                "X-Workspace-ID": str(test_workspace["id"]),
            },
            json={"name": "My Test Form"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Test Form"
        assert data["status"] == "draft"
        assert data["workspace_id"] == str(test_workspace["id"])

    def test_list_forms(
        self, client: TestClient, test_user: dict, test_workspace: dict, db_session
    ):
        """Test listing forms."""
        from tests.fixtures.factories import create_form

        form = create_form(
            db_session,
            workspace_id=test_workspace["id"],
            name="Test Form",
            created_by=test_user["id"],
        )

        response = client.get(
            f"/api/v1/workspaces/{test_workspace['id']}/forms",
            headers={
                **test_user["token_header"],
                "X-Workspace-ID": str(test_workspace["id"]),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert any(f["id"] == str(form.id) for f in data)

    def test_get_form(
        self, client: TestClient, test_user: dict, test_workspace: dict, db_session
    ):
        """Test getting form details."""
        from tests.fixtures.factories import create_form

        form = create_form(
            db_session,
            workspace_id=test_workspace["id"],
            name="Test Form",
            created_by=test_user["id"],
        )

        response = client.get(
            f"/api/v1/workspaces/{test_workspace['id']}/forms/{form.id}",
            headers={
                **test_user["token_header"],
                "X-Workspace-ID": str(test_workspace["id"]),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Form"

    def test_update_form(
        self, client: TestClient, test_user: dict, test_workspace: dict, db_session
    ):
        """Test updating a form."""
        from tests.fixtures.factories import create_form

        form = create_form(
            db_session,
            workspace_id=test_workspace["id"],
            name="Old Name",
            created_by=test_user["id"],
        )

        response = client.patch(
            f"/api/v1/workspaces/{test_workspace['id']}/forms/{form.id}",
            headers={
                **test_user["token_header"],
                "X-Workspace-ID": str(test_workspace["id"]),
            },
            json={"name": "New Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"


class TestFormPublishing:
    """Test form publishing endpoints."""

    def test_publish_form(
        self, client: TestClient, test_user: dict, test_workspace: dict, db_session
    ):
        """Test publishing a form."""
        from tests.fixtures.factories import create_form

        form = create_form(
            db_session,
            workspace_id=test_workspace["id"],
            name="Test Form",
            created_by=test_user["id"],
            status="draft",
        )

        response = client.post(
            f"/api/v1/workspaces/{test_workspace['id']}/forms/{form.id}/publish",
            headers={
                **test_user["token_header"],
                "X-Workspace-ID": str(test_workspace["id"]),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"

    def test_unpublish_form(
        self, client: TestClient, test_user: dict, test_workspace: dict, db_session
    ):
        """Test unpublishing a form."""
        from tests.fixtures.factories import create_form

        form = create_form(
            db_session,
            workspace_id=test_workspace["id"],
            name="Test Form",
            created_by=test_user["id"],
            status="published",
        )

        response = client.post(
            f"/api/v1/workspaces/{test_workspace['id']}/forms/{form.id}/unpublish",
            headers={
                **test_user["token_header"],
                "X-Workspace-ID": str(test_workspace["id"]),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "draft"

    def test_archive_form(
        self, client: TestClient, test_user: dict, test_workspace: dict, db_session
    ):
        """Test archiving a form."""
        from tests.fixtures.factories import create_form

        form = create_form(
            db_session,
            workspace_id=test_workspace["id"],
            name="Test Form",
            created_by=test_user["id"],
        )

        response = client.post(
            f"/api/v1/workspaces/{test_workspace['id']}/forms/{form.id}/archive",
            headers={
                **test_user["token_header"],
                "X-Workspace-ID": str(test_workspace["id"]),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "archived"


class TestFormDefinition:
    """Test form definition endpoints."""

    def test_update_form_definition(
        self, client: TestClient, test_user: dict, test_workspace: dict, db_session
    ):
        """Test updating form definition."""
        from tests.fixtures.factories import create_form

        form = create_form(
            db_session,
            workspace_id=test_workspace["id"],
            name="Test Form",
            created_by=test_user["id"],
        )

        new_definition = {
            "fields": [{"type": "short_text", "title": "Name", "required": True}]
        }

        response = client.put(
            f"/api/v1/workspaces/{test_workspace['id']}/forms/{form.id}/definition",
            headers={
                **test_user["token_header"],
                "X-Workspace-ID": str(test_workspace["id"]),
            },
            json={"definition": new_definition},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["definition_jsonb"] == new_definition
