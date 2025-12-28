"""PostgreSQL implementation of submission repositories."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.db.models import Answer as AnswerModel
from app.core.db.models import Submission as SubmissionModel
from app.modules.submissions.domain.entities import Answer, Submission
from app.modules.submissions.domain.repositories import (
    AnswerRepository,
    SubmissionRepository,
)


def _submission_model_to_entity(db_submission: SubmissionModel) -> Submission:
    """Convert Submission model to domain entity."""
    return Submission(
        id=db_submission.id,
        form_id=db_submission.form_id,
        form_version_id=db_submission.form_version_id,
        workspace_id=db_submission.workspace_id,
        ip_address=db_submission.ip_address,
        user_agent=db_submission.user_agent,
        source=db_submission.source,
        created_at=db_submission.created_at,
    )


def _answer_model_to_entity(db_answer: AnswerModel) -> Answer:
    """Convert Answer model to domain entity."""
    return Answer(
        id=db_answer.id,
        submission_id=db_answer.submission_id,
        field_ref=db_answer.field_ref,
        field_type=db_answer.field_type,
        value_jsonb=db_answer.value_jsonb,
        value_text=db_answer.value_text,
        value_number=db_answer.value_number,
        value_bool=db_answer.value_bool,
        value_time=db_answer.value_time,
        choice_ids=db_answer.choice_ids,
    )


class PostgreSQLSubmissionRepository(SubmissionRepository):
    """PostgreSQL implementation of SubmissionRepository."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, submission: Submission) -> Submission:
        """Create a new submission."""
        db_submission = SubmissionModel(
            form_id=submission.form_id,
            form_version_id=submission.form_version_id,
            workspace_id=submission.workspace_id,
            ip_address=submission.ip_address,
            user_agent=submission.user_agent,
            source=submission.source,
        )
        self.db.add(db_submission)
        self.db.commit()
        self.db.refresh(db_submission)
        return _submission_model_to_entity(db_submission)

    def get_by_id(self, submission_id: UUID) -> Submission | None:
        """Get submission by ID."""
        db_submission = (
            self.db.query(SubmissionModel)
            .filter(SubmissionModel.id == submission_id)
            .first()
        )
        if not db_submission:
            return None
        return _submission_model_to_entity(db_submission)

    def list_by_form(self, form_id: UUID) -> list[Submission]:
        """List submissions for a form."""
        db_submissions = (
            self.db.query(SubmissionModel)
            .filter(SubmissionModel.form_id == form_id)
            .order_by(SubmissionModel.created_at.desc())
            .all()
        )
        return [_submission_model_to_entity(s) for s in db_submissions]

    def list_by_form_version(self, form_version_id: UUID) -> list[Submission]:
        """List submissions for a specific form version."""
        db_submissions = (
            self.db.query(SubmissionModel)
            .filter(SubmissionModel.form_version_id == form_version_id)
            .order_by(SubmissionModel.created_at.desc())
            .all()
        )
        return [_submission_model_to_entity(s) for s in db_submissions]

    def list_by_workspace(self, workspace_id: UUID) -> list[Submission]:
        """List submissions for a workspace."""
        db_submissions = (
            self.db.query(SubmissionModel)
            .filter(SubmissionModel.workspace_id == workspace_id)
            .order_by(SubmissionModel.created_at.desc())
            .all()
        )
        return [_submission_model_to_entity(s) for s in db_submissions]

    def delete(self, submission_id: UUID) -> None:
        """Delete a submission."""
        db_submission = (
            self.db.query(SubmissionModel)
            .filter(SubmissionModel.id == submission_id)
            .first()
        )
        if db_submission:
            self.db.delete(db_submission)
            self.db.commit()


class PostgreSQLAnswerRepository(AnswerRepository):
    """PostgreSQL implementation of AnswerRepository."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, answer: Answer) -> Answer:
        """Create a new answer."""
        db_answer = AnswerModel(
            submission_id=answer.submission_id,
            field_ref=answer.field_ref,
            field_type=answer.field_type,
            value_jsonb=answer.value_jsonb,
            value_text=answer.value_text,
            value_number=answer.value_number,
            value_bool=answer.value_bool,
            value_time=answer.value_time,
            choice_ids=answer.choice_ids,
        )
        self.db.add(db_answer)
        self.db.commit()
        self.db.refresh(db_answer)
        return _answer_model_to_entity(db_answer)

    def create_bulk(self, answers: list[Answer]) -> list[Answer]:
        """Create multiple answers for a submission."""
        db_answers = [
            AnswerModel(
                submission_id=a.submission_id,
                field_ref=a.field_ref,
                field_type=a.field_type,
                value_jsonb=a.value_jsonb,
                value_text=a.value_text,
                value_number=a.value_number,
                value_bool=a.value_bool,
                value_time=a.value_time,
                choice_ids=a.choice_ids,
            )
            for a in answers
        ]
        self.db.add_all(db_answers)
        self.db.commit()
        for db_answer in db_answers:
            self.db.refresh(db_answer)
        return [_answer_model_to_entity(a) for a in db_answers]

    def list_by_submission(self, submission_id: UUID) -> list[Answer]:
        """List answers for a submission."""
        db_answers = (
            self.db.query(AnswerModel)
            .filter(AnswerModel.submission_id == submission_id)
            .all()
        )
        return [_answer_model_to_entity(a) for a in db_answers]

    def delete_by_submission(self, submission_id: UUID) -> None:
        """Delete all answers for a submission."""
        self.db.query(AnswerModel).filter(
            AnswerModel.submission_id == submission_id
        ).delete()
        self.db.commit()
