"""Submissions API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db.session import get_db, get_service_db
from app.core.dependencies import get_db_with_rls_context
from app.core.exceptions import NotFoundError, ValidationError
from app.modules.forms.infrastructure.repository_pg import (
    PostgreSQLFormRepository,
    PostgreSQLFormVersionRepository,
)
from app.modules.submissions.api.schemas import (
    AnswerResponse,
    SubmissionCreate,
    SubmissionResponse,
)
from app.modules.submissions.application.commands import CreateSubmissionCommand
from app.modules.submissions.application.services import SubmissionService
from app.modules.submissions.infrastructure.repository_pg import (
    PostgreSQLAnswerRepository,
    PostgreSQLSubmissionRepository,
)

router = APIRouter(tags=["submissions"])


def get_submission_service(
    db: Annotated[Session, Depends(get_db)],
) -> SubmissionService:
    """Dependency for submission service."""
    submission_repo = PostgreSQLSubmissionRepository(db)
    answer_repo = PostgreSQLAnswerRepository(db)
    form_repo = PostgreSQLFormRepository(db)
    version_repo = PostgreSQLFormVersionRepository(db)
    return SubmissionService(submission_repo, answer_repo, form_repo, version_repo)


def get_public_submission_service(
    db: Annotated[Session, Depends(get_service_db)],
) -> SubmissionService:
    """Dependency for public submission service (uses service role, bypasses RLS)."""
    submission_repo = PostgreSQLSubmissionRepository(db)
    answer_repo = PostgreSQLAnswerRepository(db)
    form_repo = PostgreSQLFormRepository(db)
    version_repo = PostgreSQLFormVersionRepository(db)
    return SubmissionService(submission_repo, answer_repo, form_repo, version_repo)


@router.post(
    "/forms/{form_id}/submissions",
    status_code=status.HTTP_201_CREATED,
    response_model=SubmissionResponse,
)
def create_submission_public(
    form_id: UUID,
    request: SubmissionCreate,
    service: Annotated[SubmissionService, Depends(get_public_submission_service)],
    db: Annotated[Session, Depends(get_service_db)],
) -> SubmissionResponse:
    """Create a public submission (no authentication required)."""
    # Convert answers dict to list format expected by the command
    answers_list = [request.answers]
    command = CreateSubmissionCommand(
        form_id=form_id,
        answers=answers_list,
        ip_address=request.ip_address,
        user_agent=request.user_agent,
        source=request.source,
    )
    try:
        submission, answers = service.create(command)
        # Fetch full submission with created_at
        from app.core.db.models import Submission as SubmissionModel

        db_submission = (
            db.query(SubmissionModel)
            .filter(SubmissionModel.id == submission.id)
            .first()
        )
        return SubmissionResponse(
            id=db_submission.id,
            form_id=db_submission.form_id,
            form_version_id=db_submission.form_version_id,
            workspace_id=db_submission.workspace_id,
            ip_address=db_submission.ip_address,
            user_agent=db_submission.user_agent,
            source=db_submission.source,
            created_at=db_submission.created_at,
            answers=[
                AnswerResponse(
                    id=a.id,
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
            ],
        )
    except (NotFoundError, ValidationError) as e:
        raise e


@router.get(
    "/workspaces/{workspace_id}/forms/{form_id}/submissions",
    response_model=list[SubmissionResponse],
)
def list_submissions(
    workspace_id: UUID,
    form_id: UUID,
    version_id: UUID | None = None,
    db: Session = Depends(get_db_with_rls_context),
) -> list[SubmissionResponse]:
    """List submissions for a form (requires authentication). Optionally filter by version_id."""
    from app.core.db.models import Answer as AnswerModel
    from app.core.db.models import Submission as SubmissionModel

    query = db.query(SubmissionModel).filter(SubmissionModel.form_id == form_id)
    if version_id:
        query = query.filter(SubmissionModel.form_version_id == version_id)

    submissions = query.all()
    result = []
    for submission in submissions:
        answers = (
            db.query(AnswerModel)
            .filter(AnswerModel.submission_id == submission.id)
            .all()
        )
        result.append(
            SubmissionResponse(
                id=submission.id,
                form_id=submission.form_id,
                form_version_id=submission.form_version_id,
                workspace_id=submission.workspace_id,
                ip_address=submission.ip_address,
                user_agent=submission.user_agent,
                source=submission.source,
                created_at=submission.created_at,
                answers=[
                    AnswerResponse(
                        id=a.id,
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
                ],
            )
        )
    return result


@router.get(
    "/workspaces/{workspace_id}/submissions",
    response_model=list[SubmissionResponse],
)
def list_workspace_submissions(
    workspace_id: UUID,
    service: Annotated[SubmissionService, Depends(get_submission_service)],
    db: Annotated[Session, Depends(get_db_with_rls_context)],
) -> list[SubmissionResponse]:
    """List all submissions for a workspace (requires authentication)."""
    from app.core.db.models import Answer as AnswerModel
    from app.core.db.models import Submission as SubmissionModel

    submissions = (
        db.query(SubmissionModel)
        .filter(SubmissionModel.workspace_id == workspace_id)
        .order_by(SubmissionModel.created_at.desc())
        .all()
    )
    result = []
    for submission in submissions:
        answers = (
            db.query(AnswerModel)
            .filter(AnswerModel.submission_id == submission.id)
            .all()
        )
        result.append(
            SubmissionResponse(
                id=submission.id,
                form_id=submission.form_id,
                form_version_id=submission.form_version_id,
                workspace_id=submission.workspace_id,
                ip_address=submission.ip_address,
                user_agent=submission.user_agent,
                source=submission.source,
                created_at=submission.created_at,
                answers=[
                    AnswerResponse(
                        id=a.id,
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
                ],
            )
        )
    return result


@router.get(
    "/workspaces/{workspace_id}/forms/{form_id}/submissions/{submission_id}",
    response_model=SubmissionResponse,
)
def get_submission(
    workspace_id: UUID,
    form_id: UUID,
    submission_id: UUID,
    db: Annotated[Session, Depends(get_db_with_rls_context)],
) -> SubmissionResponse:
    """Get submission details (requires authentication)."""
    from app.core.db.models import Submission as SubmissionModel
    from app.core.db.models import Answer as AnswerModel

    submission = (
        db.query(SubmissionModel)
        .filter(SubmissionModel.id == submission_id, SubmissionModel.form_id == form_id)
        .first()
    )
    if not submission:
        raise NotFoundError("Submission not found")

    answers = (
        db.query(AnswerModel).filter(AnswerModel.submission_id == submission.id).all()
    )
    return SubmissionResponse(
        id=submission.id,
        form_id=submission.form_id,
        form_version_id=submission.form_version_id,
        workspace_id=submission.workspace_id,
        ip_address=submission.ip_address,
        user_agent=submission.user_agent,
        source=submission.source,
        created_at=submission.created_at,
        answers=[
            AnswerResponse(
                id=a.id,
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
        ],
    )


@router.delete(
    "/workspaces/{workspace_id}/forms/{form_id}/submissions/{submission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_submission(
    workspace_id: UUID,
    form_id: UUID,
    submission_id: UUID,
    service: Annotated[SubmissionService, Depends(get_submission_service)],
    db: Annotated[Session, Depends(get_db_with_rls_context)],
) -> None:
    """Delete a submission (requires authentication)."""
    try:
        service.delete(submission_id)
    except NotFoundError as e:
        raise e
