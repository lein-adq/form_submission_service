"""Submissions domain repository interfaces."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.submissions.domain.entities import Answer, Submission


class SubmissionRepository(ABC):
    """Repository interface for submission operations."""

    @abstractmethod
    def create(self, submission: Submission) -> Submission:
        """Create a new submission."""
        pass

    @abstractmethod
    def get_by_id(self, submission_id: UUID) -> Submission | None:
        """Get submission by ID."""
        pass

    @abstractmethod
    def list_by_form(self, form_id: UUID) -> list[Submission]:
        """List submissions for a form."""
        pass

    @abstractmethod
    def list_by_form_version(self, form_version_id: UUID) -> list[Submission]:
        """List submissions for a specific form version."""
        pass

    @abstractmethod
    def list_by_workspace(self, workspace_id: UUID) -> list[Submission]:
        """List submissions for a workspace."""
        pass

    @abstractmethod
    def delete(self, submission_id: UUID) -> None:
        """Delete a submission."""
        pass


class AnswerRepository(ABC):
    """Repository interface for answer operations."""

    @abstractmethod
    def create(self, answer: Answer) -> Answer:
        """Create a new answer."""
        pass

    @abstractmethod
    def create_bulk(self, answers: list[Answer]) -> list[Answer]:
        """Create multiple answers for a submission."""
        pass

    @abstractmethod
    def list_by_submission(self, submission_id: UUID) -> list[Answer]:
        """List answers for a submission."""
        pass

    @abstractmethod
    def delete_by_submission(self, submission_id: UUID) -> None:
        """Delete all answers for a submission."""
        pass
