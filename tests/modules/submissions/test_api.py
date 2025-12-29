"""E2E tests for submission API endpoints."""

from fastapi.testclient import TestClient


class TestPublicSubmissions:
    """Test public submission endpoints (no authentication required)."""

    def test_create_submission_public(
        self, client: TestClient, test_workspace: dict, db_session
    ):
        """Test creating a public submission."""
        from tests.fixtures.factories import create_form
        from app.modules.forms.application.services import FormService
        from app.modules.forms.application.commands import PublishFormCommand
        from app.modules.forms.infrastructure.repository_pg import (
            PostgreSQLFormRepository,
            PostgreSQLFormVersionRepository,
            PostgreSQLFormFieldRepository,
            PostgreSQLFormFieldChoiceRepository,
        )

        # Create a draft form (create_form creates it with draft status)
        form = create_form(
            db_session,
            workspace_id=test_workspace["id"],
            name="Public Form",
            status="draft",
        )

        # Use FormService to properly publish the form
        # This creates version 2 as published (version 1 stays as draft)
        # This matches the actual publish flow in production
        form_repo = PostgreSQLFormRepository(db_session)
        version_repo = PostgreSQLFormVersionRepository(db_session)
        field_repo = PostgreSQLFormFieldRepository(db_session)
        choice_repo = PostgreSQLFormFieldChoiceRepository(db_session)
        form_service = FormService(form_repo, version_repo, field_repo, choice_repo)

        form_service.publish(PublishFormCommand(form_id=form.id))

        response = client.post(
            f"/api/v1/forms/{form.id}/submissions",
            json={
                "answers": {"name": "John Doe", "email": "john@example.com"},
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0",
                "source": "web",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["form_id"] == str(form.id)
        assert data["workspace_id"] == str(test_workspace["id"])

    def test_create_submission_form_not_found(self, client: TestClient):
        """Test creating submission for non-existent form."""
        from uuid import uuid4

        response = client.post(
            f"/api/v1/forms/{uuid4()}/submissions",
            json={
                "answers": {"name": "John Doe"},
            },
        )

        assert response.status_code == 404


class TestAuthenticatedSubmissions:
    """Test authenticated submission endpoints."""

    def test_list_form_submissions(
        self, client: TestClient, test_user: dict, test_workspace: dict, db_session
    ):
        """Test listing submissions for a form."""
        from tests.fixtures.factories import create_form, create_submission

        # Create form and submission
        form = create_form(
            db_session,
            workspace_id=test_workspace["id"],
            name="Test Form",
            created_by=test_user["id"],
        )

        submission = create_submission(
            db_session,
            form_id=form.id,
            form_version_id=form.draft_version_id,
            workspace_id=test_workspace["id"],
        )

        response = client.get(
            f"/api/v1/workspaces/{test_workspace['id']}/forms/{form.id}/submissions",
            headers={
                **test_user["token_header"],
                "X-Workspace-ID": str(test_workspace["id"]),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert any(s["id"] == str(submission.id) for s in data)

    def test_list_workspace_submissions(
        self, client: TestClient, test_user: dict, test_workspace: dict, db_session
    ):
        """Test listing all submissions for a workspace."""
        from tests.fixtures.factories import create_form, create_submission

        # Create form and submission
        form = create_form(
            db_session,
            workspace_id=test_workspace["id"],
            name="Test Form",
            created_by=test_user["id"],
        )

        submission = create_submission(
            db_session,
            form_id=form.id,
            form_version_id=form.draft_version_id,
            workspace_id=test_workspace["id"],
        )

        response = client.get(
            f"/api/v1/workspaces/{test_workspace['id']}/submissions",
            headers={
                **test_user["token_header"],
                "X-Workspace-ID": str(test_workspace["id"]),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert any(s["id"] == str(submission.id) for s in data)

    def test_get_submission_details(
        self, client: TestClient, test_user: dict, test_workspace: dict, db_session
    ):
        """Test getting submission details."""
        from tests.fixtures.factories import (
            create_form,
            create_submission,
            create_answer,
        )

        # Create form, submission, and answer
        form = create_form(
            db_session,
            workspace_id=test_workspace["id"],
            name="Test Form",
            created_by=test_user["id"],
        )

        submission = create_submission(
            db_session,
            form_id=form.id,
            form_version_id=form.draft_version_id,
            workspace_id=test_workspace["id"],
        )

        create_answer(
            db_session,
            submission_id=submission.id,
            field_ref="name",
            field_type="short_text",
            value_text="John Doe",
        )

        response = client.get(
            f"/api/v1/workspaces/{test_workspace['id']}/forms/{form.id}/submissions/{submission.id}",
            headers={
                **test_user["token_header"],
                "X-Workspace-ID": str(test_workspace["id"]),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(submission.id)
        assert len(data["answers"]) >= 1

    def test_delete_submission(
        self, client: TestClient, test_user: dict, test_workspace: dict, db_session
    ):
        """Test deleting a submission."""
        from tests.fixtures.factories import create_form, create_submission

        # Create form and submission
        form = create_form(
            db_session,
            workspace_id=test_workspace["id"],
            name="Test Form",
            created_by=test_user["id"],
        )

        submission = create_submission(
            db_session,
            form_id=form.id,
            form_version_id=form.draft_version_id,
            workspace_id=test_workspace["id"],
        )

        response = client.delete(
            f"/api/v1/workspaces/{test_workspace['id']}/forms/{form.id}/submissions/{submission.id}",
            headers={
                **test_user["token_header"],
                "X-Workspace-ID": str(test_workspace["id"]),
            },
        )

        assert response.status_code == 204

    def test_list_submissions_no_auth(self, client: TestClient, test_workspace: dict):
        """Test listing submissions without authentication."""
        response = client.get(
            f"/api/v1/workspaces/{test_workspace['id']}/submissions",
        )

        assert response.status_code == 401
