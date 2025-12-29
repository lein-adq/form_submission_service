"""Integration tests for RLS (Row-Level Security) isolation."""

from fastapi.testclient import TestClient


class TestRLSWorkspaceIsolation:
    """Test RLS isolation between workspaces."""

    def test_user_cannot_access_other_workspace_forms(
        self,
        client: TestClient,
        test_user: dict,
        test_workspace: dict,
        test_workspace2: dict,
        db_session,
    ):
        """Test user cannot access forms from workspace they're not a member of."""
        from tests.fixtures.factories import create_form

        # Create form in workspace2 (user is not a member)
        form = create_form(
            db_session,
            workspace_id=test_workspace2["id"],
            name="Other Workspace Form",
        )

        # Try to access form in workspace2 using workspace1 context
        response = client.get(
            f"/api/v1/workspaces/{test_workspace2['id']}/forms/{form.id}",
            headers={
                **test_user["token_header"],
                "X-Workspace-ID": str(test_workspace2["id"]),
            },
        )

        # Should fail due to RLS - user is not member of workspace2
        # RLS should prevent access, returning 403 or 404
        assert response.status_code in [403, 404], (
            f"Expected 403 or 404, got {response.status_code}. "
            f"Response: {response.json() if response.status_code == 200 else response.text}"
        )

    def test_user_cannot_list_other_workspace_forms(
        self,
        client: TestClient,
        test_user: dict,
        test_workspace: dict,
        test_workspace2: dict,
        db_session,
    ):
        """Test user cannot list forms from workspace they're not a member of."""
        from tests.fixtures.factories import create_form

        # Create form in workspace2
        form = create_form(
            db_session,
            workspace_id=test_workspace2["id"],
            name="Other Workspace Form",
        )

        # Try to list forms in workspace2
        response = client.get(
            f"/api/v1/workspaces/{test_workspace2['id']}/forms",
            headers={
                **test_user["token_header"],
                "X-Workspace-ID": str(test_workspace2["id"]),
            },
        )

        # Should fail due to RLS - user is not member of workspace2
        # RLS should prevent access, returning 403 or 404, or empty list
        if response.status_code == 200:
            data = response.json()
            # Form from workspace2 should not appear in the list
            assert not any(f["id"] == str(form.id) for f in data), (
                f"Form from workspace2 should not be accessible. "
                f"Found forms: {[f['id'] for f in data]}"
            )
        else:
            # If not 200, should be 403 or 404
            assert response.status_code in [403, 404], (
                f"Expected 200, 403, or 404, got {response.status_code}. "
                f"Response: {response.text}"
            )

    def test_user_cannot_access_other_workspace_submissions(
        self,
        client: TestClient,
        test_user: dict,
        test_workspace: dict,
        test_workspace2: dict,
        db_session,
    ):
        """Test user cannot access submissions from other workspaces."""
        from tests.fixtures.factories import create_form, create_submission

        # Create form and submission in workspace2
        form = create_form(
            db_session,
            workspace_id=test_workspace2["id"],
            name="Other Workspace Form",
        )

        submission = create_submission(
            db_session,
            form_id=form.id,
            form_version_id=form.draft_version_id,
            workspace_id=test_workspace2["id"],
        )

        # Try to access submission
        response = client.get(
            f"/api/v1/workspaces/{test_workspace2['id']}/forms/{form.id}/submissions/{submission.id}",
            headers={
                **test_user["token_header"],
                "X-Workspace-ID": str(test_workspace2["id"]),
            },
        )

        # Should fail due to RLS - user is not member of workspace2
        # RLS should prevent access, returning 403 or 404
        assert response.status_code in [403, 404], (
            f"Expected 403 or 404, got {response.status_code}. "
            f"Response: {response.json() if response.status_code == 200 else response.text}"
        )

    def test_workspace_member_can_access_workspace_data(
        self,
        client: TestClient,
        test_user: dict,
        test_user2: dict,
        test_workspace: dict,
        db_session,
    ):
        """Test that workspace members can access workspace data."""
        from tests.fixtures.factories import (
            create_workspace_member,
            create_form,
        )

        # Add user2 as member of workspace
        create_workspace_member(
            db_session, test_workspace["id"], test_user2["id"], "viewer"
        )

        # Create form in workspace
        form = create_form(
            db_session,
            workspace_id=test_workspace["id"],
            name="Workspace Form",
            created_by=test_user["id"],
        )

        # User2 should be able to access the form
        response = client.get(
            f"/api/v1/workspaces/{test_workspace['id']}/forms/{form.id}",
            headers={
                **test_user2["token_header"],
                "X-Workspace-ID": str(test_workspace["id"]),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(form.id)


class TestRLSDataLeakPrevention:
    """Test that RLS prevents data leaks across workspaces."""

    def test_listing_all_workspaces_only_shows_user_workspaces(
        self,
        client: TestClient,
        test_user: dict,
        test_user2: dict,
        test_workspace: dict,
        test_workspace2: dict,
    ):
        """Test that listing workspaces only shows workspaces user is member of."""
        # test_user is member of test_workspace
        # test_user2 is member of test_workspace2

        response = client.get(
            "/api/v1/workspaces",
            headers=test_user["token_header"],
        )

        assert response.status_code == 200
        data = response.json()

        # Should include test_workspace
        assert any(w["id"] == str(test_workspace["id"]) for w in data)

        # Should NOT include test_workspace2
        assert not any(w["id"] == str(test_workspace2["id"]) for w in data)

    def test_rls_context_is_set_correctly(self, db_session, rls_context):
        """Test that RLS context variables are set in database session."""
        from tests.fixtures.database import verify_rls_context

        context = verify_rls_context(db_session)

        assert context["user_id"] == str(rls_context["user_id"])
        assert context["workspace_id"] == str(rls_context["workspace_id"])

    def test_cross_workspace_form_access_prevented(
        self,
        client: TestClient,
        test_user: dict,
        test_user2: dict,
        test_workspace: dict,
        test_workspace2: dict,
        db_session,
    ):
        """Test comprehensive cross-workspace access prevention."""
        from tests.fixtures.factories import create_form

        # User1 creates form in workspace1
        form1 = create_form(
            db_session,
            workspace_id=test_workspace["id"],
            name="Workspace 1 Form",
            created_by=test_user["id"],
        )

        # User2 creates form in workspace2
        form2 = create_form(
            db_session,
            workspace_id=test_workspace2["id"],
            name="Workspace 2 Form",
            created_by=test_user2["id"],
        )

        # User1 tries to access form from workspace2
        response1 = client.get(
            f"/api/v1/workspaces/{test_workspace2['id']}/forms/{form2.id}",
            headers={
                **test_user["token_header"],
                "X-Workspace-ID": str(test_workspace2["id"]),
            },
        )
        assert response1.status_code in [403, 404], (
            f"User1 should not access workspace2 form. "
            f"Expected 403 or 404, got {response1.status_code}. "
            f"Response: {response1.json() if response1.status_code == 200 else response1.text}"
        )

        # User2 tries to access form from workspace1
        response2 = client.get(
            f"/api/v1/workspaces/{test_workspace['id']}/forms/{form1.id}",
            headers={
                **test_user2["token_header"],
                "X-Workspace-ID": str(test_workspace["id"]),
            },
        )
        assert response2.status_code in [403, 404], (
            f"User2 should not access workspace1 form. "
            f"Expected 403 or 404, got {response2.status_code}. "
            f"Response: {response2.json() if response2.status_code == 200 else response2.text}"
        )

        # Each user should only access their own workspace's forms
        response3 = client.get(
            f"/api/v1/workspaces/{test_workspace['id']}/forms/{form1.id}",
            headers={
                **test_user["token_header"],
                "X-Workspace-ID": str(test_workspace["id"]),
            },
        )
        assert response3.status_code == 200

        response4 = client.get(
            f"/api/v1/workspaces/{test_workspace2['id']}/forms/{form2.id}",
            headers={
                **test_user2["token_header"],
                "X-Workspace-ID": str(test_workspace2["id"]),
            },
        )
        assert response4.status_code == 200
