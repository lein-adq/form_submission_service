"""Unit tests for submission services."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError, ValidationError
from app.modules.submissions.application.commands import CreateSubmissionCommand
from app.modules.submissions.application.services import SubmissionService
from app.modules.submissions.domain.entities import Answer, Submission
from app.modules.forms.domain.entities import Form, FormVersion


class TestSubmissionService:
    """Test SubmissionService business logic."""

    def test_create_submission_success(self):
        """Test creating a submission."""
        mock_submission_repo = Mock()
        mock_answer_repo = Mock()
        mock_form_repo = Mock()
        mock_version_repo = Mock()

        form_id = uuid4()
        version_id = uuid4()
        workspace_id = uuid4()

        # Mock form and version
        form = Form(
            id=form_id,
            workspace_id=workspace_id,
            name="Test Form",
            status="published",
            created_by=uuid4(),
            draft_version_id=uuid4(),
            published_version_id=version_id,
            folder_id=None,
        )
        version = FormVersion(
            id=version_id,
            form_id=form_id,
            version_number=1,
            state="published",
            definition_jsonb={"fields": []},
            created_by=uuid4(),
        )

        mock_form_repo.get_by_id.return_value = form
        mock_version_repo.get_by_id.return_value = version

        # Mock submission
        submission = Submission(
            id=uuid4(),
            form_id=form_id,
            form_version_id=version_id,
            workspace_id=workspace_id,
            ip_address="192.168.1.1",
            user_agent="TestAgent",
            source="web",
        )
        mock_submission_repo.create.return_value = submission

        # Mock answers
        answer = Answer(
            id=uuid4(),
            submission_id=submission.id,
            field_ref="name",
            field_type="short_text",
            value_text="John Doe",
            value_jsonb=None,
            value_number=None,
            value_bool=None,
            value_time=None,
            choice_ids=None,
        )
        mock_answer_repo.create.return_value = answer

        service = SubmissionService(
            mock_submission_repo,
            mock_answer_repo,
            mock_form_repo,
            mock_version_repo,
        )

        command = CreateSubmissionCommand(
            form_id=form_id,
            answers=[{"name": "John Doe"}],
            ip_address="192.168.1.1",
            user_agent="TestAgent",
            source="web",
        )

        result_submission, result_answers = service.create(command)

        assert result_submission.form_id == form_id
        assert len(result_answers) >= 0
        mock_submission_repo.create.assert_called_once()

    def test_create_submission_form_not_published(self):
        """Test creating submission for unpublished form fails."""
        mock_submission_repo = Mock()
        mock_answer_repo = Mock()
        mock_form_repo = Mock()
        mock_version_repo = Mock()

        form_id = uuid4()

        # Mock form with draft status
        form = Form(
            id=form_id,
            workspace_id=uuid4(),
            name="Test Form",
            status="draft",  # Not published
            created_by=uuid4(),
            draft_version_id=uuid4(),
            published_version_id=None,
            folder_id=None,
        )

        mock_form_repo.get_by_id.return_value = form

        service = SubmissionService(
            mock_submission_repo,
            mock_answer_repo,
            mock_form_repo,
            mock_version_repo,
        )

        command = CreateSubmissionCommand(
            form_id=form_id,
            answers=[{"name": "John Doe"}],
        )

        with pytest.raises(ValidationError):
            service.create(command)

    def test_create_submission_form_not_found(self):
        """Test creating submission for non-existent form."""
        mock_submission_repo = Mock()
        mock_answer_repo = Mock()
        mock_form_repo = Mock()
        mock_version_repo = Mock()

        mock_form_repo.get_by_id.return_value = None

        service = SubmissionService(
            mock_submission_repo,
            mock_answer_repo,
            mock_form_repo,
            mock_version_repo,
        )

        command = CreateSubmissionCommand(
            form_id=uuid4(),
            answers=[{"name": "John Doe"}],
        )

        with pytest.raises(NotFoundError):
            service.create(command)

    def test_delete_submission(self):
        """Test deleting a submission."""
        mock_submission_repo = Mock()
        mock_answer_repo = Mock()
        mock_form_repo = Mock()
        mock_version_repo = Mock()

        submission_id = uuid4()
        submission = Submission(
            id=submission_id,
            form_id=uuid4(),
            form_version_id=uuid4(),
            workspace_id=uuid4(),
            ip_address=None,
            user_agent=None,
            source="web",
        )

        mock_submission_repo.get_by_id.return_value = submission

        service = SubmissionService(
            mock_submission_repo,
            mock_answer_repo,
            mock_form_repo,
            mock_version_repo,
        )

        service.delete(submission_id)

        mock_submission_repo.delete.assert_called_once_with(submission_id)
