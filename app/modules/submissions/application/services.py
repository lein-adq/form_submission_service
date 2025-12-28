"""Submissions application services."""

from uuid import UUID

from app.core.exceptions import NotFoundError, ValidationError
from app.modules.forms.domain.repositories import FormRepository, FormVersionRepository
from app.modules.submissions.application.commands import CreateSubmissionCommand
from app.modules.submissions.domain.entities import Answer, Submission
from app.modules.submissions.domain.policies import can_accept_submission
from app.modules.submissions.domain.repositories import (
    AnswerRepository,
    SubmissionRepository,
)


class SubmissionService:
    """Service for submission operations."""

    def __init__(
        self,
        submission_repository: SubmissionRepository,
        answer_repository: AnswerRepository,
        form_repository: FormRepository,
        version_repository: FormVersionRepository,
    ) -> None:
        self.submission_repository = submission_repository
        self.answer_repository = answer_repository
        self.form_repository = form_repository
        self.version_repository = version_repository

    def create(
        self, command: CreateSubmissionCommand
    ) -> tuple[Submission, list[Answer]]:
        """Create a new submission with answers (public endpoint)."""
        # Verify form exists and is published
        form = self.form_repository.get_by_id(command.form_id)
        if not form:
            raise NotFoundError("Form not found")

        if not can_accept_submission(form):
            raise ValidationError("Form is not published and cannot accept submissions")

        # Get the published version
        published_version = self.version_repository.get_published(command.form_id)
        if not published_version:
            raise ValidationError("Form has no published version")

        # Create submission with form_version_id and workspace_id
        submission = Submission(
            id=UUID(int=0),  # Will be set by repository
            form_id=command.form_id,
            form_version_id=published_version.id,
            workspace_id=form.workspace_id,
            ip_address=command.ip_address,
            user_agent=command.user_agent,
            source=command.source,
        )
        created_submission = self.submission_repository.create(submission)

        # Create answers with rich value storage
        answers = []
        for answer_data in command.answers:
            if isinstance(answer_data, dict):
                for field_ref, value in answer_data.items():
                    answer = self._create_answer_from_value(
                        created_submission.id, field_ref, value
                    )
                    created_answer = self.answer_repository.create(answer)
                    answers.append(created_answer)

        return created_submission, answers

    def _create_answer_from_value(
        self, submission_id: UUID, field_ref: str, value: str | None
    ) -> Answer:
        """Create an Answer entity from a field ref and value."""
        from app.core.domain.value_objects import FieldType

        # For now, default to SHORT_TEXT and store as value_text
        # In a full implementation, you'd look up the field from form_fields
        # to get the correct field_type
        answer = Answer(
            id=UUID(int=0),  # Will be set by repository
            submission_id=submission_id,
            field_ref=field_ref,
            field_type=FieldType.SHORT_TEXT,
            value_text=str(value) if value is not None else None,
            value_jsonb={"value": value} if value is not None else None,
        )
        return answer

    def get_by_id(self, submission_id: UUID) -> Submission:
        """Get submission by ID."""
        submission = self.submission_repository.get_by_id(submission_id)
        if not submission:
            raise NotFoundError("Submission not found")
        return submission

    def list_by_form(self, form_id: UUID) -> list[Submission]:
        """List submissions for a form."""
        return self.submission_repository.list_by_form(form_id)

    def get_answers_for_submission(self, submission_id: UUID) -> list[Answer]:
        """Get answers for a submission."""
        return self.answer_repository.list_by_submission(submission_id)

    def delete(self, submission_id: UUID) -> None:
        """Delete a submission and its answers."""
        submission = self.submission_repository.get_by_id(submission_id)
        if not submission:
            raise NotFoundError("Submission not found")

        # Delete answers first (cascade would handle this, but being explicit)
        self.answer_repository.delete_by_submission(submission_id)
        self.submission_repository.delete(submission_id)

    def list_by_workspace(self, workspace_id: UUID) -> list[Submission]:
        """List all submissions for a workspace."""
        return self.submission_repository.list_by_workspace(workspace_id)

    def list_by_form_version(self, form_version_id: UUID) -> list[Submission]:
        """List submissions for a specific form version."""
        return self.submission_repository.list_by_form_version(form_version_id)
