"""Unit tests for form services."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationError
from app.modules.forms.application.commands import (
    ArchiveFormCommand,
    CreateFormCommand,
    PublishFormCommand,
    UnpublishFormCommand,
    UpdateFormCommand,
    UpdateFormDefinitionCommand,
)
from app.modules.forms.application.services import FormService
from app.modules.forms.domain.entities import Form, FormVersion


class TestFormService:
    """Test FormService business logic."""

    def test_create_form(self):
        """Test creating a form."""
        mock_form_repo = Mock()
        mock_version_repo = Mock()
        mock_field_repo = Mock()
        mock_choice_repo = Mock()

        form_id = uuid4()
        workspace_id = uuid4()
        user_id = uuid4()

        form = Form(
            id=form_id,
            workspace_id=workspace_id,
            name="Test Form",
            status="draft",
            created_by=user_id,
            draft_version_id=None,
            published_version_id=None,
            folder_id=None,
        )
        version = FormVersion(
            id=uuid4(),
            form_id=form_id,
            version_number=1,
            state="draft",
            definition_jsonb={},
            created_by=user_id,
        )

        # Mock the create calls
        mock_form_repo.create.return_value = form
        mock_version_repo.create.return_value = version

        # Mock update to return form with draft_version_id set
        updated_form = Form(
            id=form_id,
            workspace_id=workspace_id,
            name="Test Form",
            status="draft",
            created_by=user_id,
            draft_version_id=version.id,
            published_version_id=None,
            folder_id=None,
        )
        mock_form_repo.update.return_value = updated_form

        service = FormService(
            mock_form_repo, mock_version_repo, mock_field_repo, mock_choice_repo
        )
        command = CreateFormCommand(
            workspace_id=workspace_id,
            name="Test Form",
            created_by=user_id,
        )

        result = service.create(command)

        assert result.name == "Test Form"
        assert result.status == "draft"
        mock_form_repo.create.assert_called_once()
        mock_version_repo.create.assert_called_once()

    def test_update_form(self):
        """Test updating a form."""
        mock_form_repo = Mock()
        mock_version_repo = Mock()
        mock_field_repo = Mock()
        mock_choice_repo = Mock()

        form_id = uuid4()
        form = Form(
            id=form_id,
            workspace_id=uuid4(),
            name="Old Name",
            status="draft",
            created_by=uuid4(),
            draft_version_id=None,
            published_version_id=None,
            folder_id=None,
        )

        mock_form_repo.get_by_id.return_value = form

        # Mock update to return form with updated name
        updated_form = Form(
            id=form_id,
            workspace_id=form.workspace_id,
            name="New Name",
            status=form.status,
            created_by=form.created_by,
            draft_version_id=form.draft_version_id,
            published_version_id=form.published_version_id,
            folder_id=form.folder_id,
        )
        mock_form_repo.update.return_value = updated_form

        service = FormService(
            mock_form_repo, mock_version_repo, mock_field_repo, mock_choice_repo
        )
        command = UpdateFormCommand(form_id=form_id, name="New Name")

        result = service.update(command)

        assert result.name == "New Name"
        mock_form_repo.update.assert_called_once()

    def test_publish_form_success(self):
        """Test publishing a form."""
        mock_form_repo = Mock()
        mock_version_repo = Mock()
        mock_field_repo = Mock()
        mock_choice_repo = Mock()

        form_id = uuid4()
        version_id = uuid4()

        draft_version = FormVersion(
            id=version_id,
            form_id=form_id,
            version_number=1,
            state="draft",
            definition_jsonb={"fields": []},
            created_by=uuid4(),
        )

        form = Form(
            id=form_id,
            workspace_id=uuid4(),
            name="Test Form",
            status="draft",
            created_by=uuid4(),
            draft_version_id=version_id,
            published_version_id=None,
            folder_id=None,
        )

        mock_form_repo.get_by_id.return_value = form
        mock_version_repo.get_draft.return_value = draft_version

        # Mock version create to return a new published version
        published_version = FormVersion(
            id=uuid4(),
            form_id=form_id,
            version_number=2,
            state="published",
            definition_jsonb=draft_version.definition_jsonb,
            created_by=form.created_by,
        )
        mock_version_repo.create.return_value = published_version

        # Mock form update to return form with published status
        updated_form = Form(
            id=form_id,
            workspace_id=form.workspace_id,
            name=form.name,
            status="published",
            created_by=form.created_by,
            draft_version_id=form.draft_version_id,
            published_version_id=published_version.id,
            folder_id=form.folder_id,
        )
        mock_form_repo.update.return_value = updated_form

        service = FormService(
            mock_form_repo, mock_version_repo, mock_field_repo, mock_choice_repo
        )
        command = PublishFormCommand(form_id=form_id)

        result = service.publish(command)

        assert result.status == "published"
        mock_form_repo.update.assert_called_once()

    def test_publish_form_without_draft(self):
        """Test publishing form without draft version fails."""
        mock_form_repo = Mock()
        mock_version_repo = Mock()
        mock_field_repo = Mock()
        mock_choice_repo = Mock()

        form_id = uuid4()
        form = Form(
            id=form_id,
            workspace_id=uuid4(),
            name="Test Form",
            status="draft",
            created_by=uuid4(),
            draft_version_id=None,  # No draft version
            published_version_id=None,
            folder_id=None,
        )

        mock_form_repo.get_by_id.return_value = form
        mock_version_repo.get_draft.return_value = None  # No draft version

        service = FormService(
            mock_form_repo, mock_version_repo, mock_field_repo, mock_choice_repo
        )
        command = PublishFormCommand(form_id=form_id)

        with pytest.raises(ValidationError):
            service.publish(command)

    def test_unpublish_form(self):
        """Test unpublishing a form."""
        mock_form_repo = Mock()
        mock_version_repo = Mock()
        mock_field_repo = Mock()
        mock_choice_repo = Mock()

        form_id = uuid4()
        form = Form(
            id=form_id,
            workspace_id=uuid4(),
            name="Test Form",
            status="published",
            created_by=uuid4(),
            draft_version_id=uuid4(),
            published_version_id=uuid4(),
            folder_id=None,
        )

        mock_form_repo.get_by_id.return_value = form

        # Mock update to return form with draft status
        updated_form = Form(
            id=form_id,
            workspace_id=form.workspace_id,
            name=form.name,
            status="draft",
            created_by=form.created_by,
            draft_version_id=form.draft_version_id,
            published_version_id=form.published_version_id,
            folder_id=form.folder_id,
        )
        mock_form_repo.update.return_value = updated_form

        service = FormService(
            mock_form_repo, mock_version_repo, mock_field_repo, mock_choice_repo
        )
        command = UnpublishFormCommand(form_id=form_id)

        result = service.unpublish(command)

        assert result.status == "draft"
        mock_form_repo.update.assert_called_once()

    def test_archive_form(self):
        """Test archiving a form."""
        mock_form_repo = Mock()
        mock_version_repo = Mock()
        mock_field_repo = Mock()
        mock_choice_repo = Mock()

        form_id = uuid4()
        form = Form(
            id=form_id,
            workspace_id=uuid4(),
            name="Test Form",
            status="published",
            created_by=uuid4(),
            draft_version_id=uuid4(),
            published_version_id=uuid4(),
            folder_id=None,
        )

        mock_form_repo.get_by_id.return_value = form

        # Mock archive to return archived form
        archived_form = Form(
            id=form_id,
            workspace_id=form.workspace_id,
            name=form.name,
            status="archived",
            created_by=form.created_by,
            draft_version_id=form.draft_version_id,
            published_version_id=form.published_version_id,
            folder_id=form.folder_id,
        )
        mock_form_repo.archive.return_value = archived_form

        service = FormService(
            mock_form_repo, mock_version_repo, mock_field_repo, mock_choice_repo
        )
        command = ArchiveFormCommand(form_id=form_id)

        result = service.archive(command)

        assert result.status == "archived"
        mock_form_repo.archive.assert_called_once()

    def test_update_form_definition(self):
        """Test updating form definition."""
        mock_form_repo = Mock()
        mock_version_repo = Mock()
        mock_field_repo = Mock()
        mock_choice_repo = Mock()

        form_id = uuid4()
        version_id = uuid4()

        form = Form(
            id=form_id,
            workspace_id=uuid4(),
            name="Test Form",
            status="draft",
            created_by=uuid4(),
            draft_version_id=version_id,
            published_version_id=None,
            folder_id=None,
        )

        version = FormVersion(
            id=version_id,
            form_id=form_id,
            version_number=1,
            state="draft",
            definition_jsonb={},
            created_by=uuid4(),
        )

        mock_form_repo.get_by_id.return_value = form
        mock_version_repo.get_draft.return_value = version

        # Mock update to return version with updated definition
        updated_version = FormVersion(
            id=version_id,
            form_id=form_id,
            version_number=version.version_number,
            state=version.state,
            definition_jsonb={"fields": [{"type": "text", "title": "Name"}]},
            created_by=version.created_by,
        )
        mock_version_repo.update.return_value = updated_version

        service = FormService(
            mock_form_repo, mock_version_repo, mock_field_repo, mock_choice_repo
        )

        new_definition = {"fields": [{"type": "text", "title": "Name"}]}
        command = UpdateFormDefinitionCommand(
            form_id=form_id,
            definition=new_definition,
        )

        result = service.update_definition(command)

        assert result.definition_jsonb == new_definition
        mock_version_repo.update.assert_called_once()
