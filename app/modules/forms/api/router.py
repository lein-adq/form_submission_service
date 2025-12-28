"""Forms API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.core.dependencies import get_db_with_rls_context, get_current_user
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security.indentity import Identity
from app.modules.forms.api.schemas import (
    FormCreate,
    FormDefinitionUpdate,
    FormDuplicateRequest,
    FormFieldResponse,
    FormMoveRequest,
    FormResponse,
    FormUpdate,
    FormVersionResponse,
)
from app.modules.forms.application.commands import (
    ArchiveFormCommand,
    CreateFormCommand,
    DuplicateFormCommand,
    MoveFormToFolderCommand,
    PublishFormCommand,
    UnpublishFormCommand,
    UpdateFormCommand,
    UpdateFormDefinitionCommand,
)
from app.modules.forms.application.services import FormService
from app.modules.forms.infrastructure.repository_pg import (
    PostgreSQLFormFieldChoiceRepository,
    PostgreSQLFormFieldRepository,
    PostgreSQLFormRepository,
    PostgreSQLFormVersionRepository,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/forms", tags=["forms"])


def get_form_service(db: Annotated[Session, Depends(get_db)]) -> FormService:
    """Dependency for form service."""
    form_repo = PostgreSQLFormRepository(db)
    version_repo = PostgreSQLFormVersionRepository(db)
    field_repo = PostgreSQLFormFieldRepository(db)
    choice_repo = PostgreSQLFormFieldChoiceRepository(db)
    return FormService(form_repo, version_repo, field_repo, choice_repo)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=FormResponse)
def create_form(
    workspace_id: UUID,
    request: FormCreate,
    identity: Annotated[Identity, Depends(get_current_user)],
    service: Annotated[FormService, Depends(get_form_service)],
    db: Annotated[Session, Depends(get_db_with_rls_context)],
) -> FormResponse:
    """Create a new form."""
    command = CreateFormCommand(
        workspace_id=workspace_id,
        name=request.name,
        created_by=identity.user_id,
    )
    form = service.create(command)
    # Fetch full form with created_at
    from app.core.db.models import Form as FormModel

    db_form = db.query(FormModel).filter(FormModel.id == form.id).first()
    return FormResponse(
        id=db_form.id,
        workspace_id=db_form.workspace_id,
        folder_id=db_form.folder_id,
        name=db_form.name,
        status=db_form.status,
        draft_version_id=db_form.draft_version_id,
        published_version_id=db_form.published_version_id,
        created_by=db_form.created_by,
        created_at=db_form.created_at,
    )


@router.get("", response_model=list[FormResponse])
def list_forms(
    workspace_id: UUID,
    db: Annotated[Session, Depends(get_db_with_rls_context)],
) -> list[FormResponse]:
    """List forms for a workspace."""
    from app.core.db.models import Form as FormModel

    forms = db.query(FormModel).filter(FormModel.workspace_id == workspace_id).all()
    return [
        FormResponse(
            id=f.id,
            workspace_id=f.workspace_id,
            name=f.name,
            status=f.status,
            created_by=f.created_by,
            created_at=f.created_at,
        )
        for f in forms
    ]


@router.get("/{form_id}", response_model=FormResponse)
def get_form(
    workspace_id: UUID,
    form_id: UUID,
    db: Annotated[Session, Depends(get_db_with_rls_context)],
) -> FormResponse:
    """Get form details."""
    from app.core.db.models import Form as FormModel

    form = (
        db.query(FormModel)
        .filter(FormModel.id == form_id, FormModel.workspace_id == workspace_id)
        .first()
    )
    if not form:
        raise NotFoundError("Form not found")
    return FormResponse(
        id=form.id,
        workspace_id=form.workspace_id,
        name=form.name,
        status=form.status,
        created_by=form.created_by,
        created_at=form.created_at,
    )


@router.patch("/{form_id}", response_model=FormResponse)
def update_form(
    workspace_id: UUID,
    form_id: UUID,
    request: FormUpdate,
    service: Annotated[FormService, Depends(get_form_service)],
    db: Annotated[Session, Depends(get_db_with_rls_context)],
) -> FormResponse:
    """Update a form."""
    command = UpdateFormCommand(form_id=form_id, name=request.name)
    try:
        form = service.update(command)
        # Fetch full form with created_at
        from app.core.db.models import Form as FormModel

        db_form = db.query(FormModel).filter(FormModel.id == form.id).first()
        return FormResponse(
            id=db_form.id,
            workspace_id=db_form.workspace_id,
            name=db_form.name,
            status=db_form.status,
            created_by=db_form.created_by,
            created_at=db_form.created_at,
        )
    except NotFoundError as e:
        raise e


@router.post("/{form_id}/publish", response_model=FormResponse)
def publish_form(
    workspace_id: UUID,
    form_id: UUID,
    service: Annotated[FormService, Depends(get_form_service)],
    db: Annotated[Session, Depends(get_db_with_rls_context)],
) -> FormResponse:
    """Publish a form."""
    command = PublishFormCommand(form_id=form_id)
    try:
        form = service.publish(command)
        # Fetch full form with created_at
        from app.core.db.models import Form as FormModel

        db_form = db.query(FormModel).filter(FormModel.id == form.id).first()
        return FormResponse(
            id=db_form.id,
            workspace_id=db_form.workspace_id,
            name=db_form.name,
            status=db_form.status,
            created_by=db_form.created_by,
            created_at=db_form.created_at,
        )
    except (NotFoundError, ValidationError) as e:
        raise e


@router.post("/{form_id}/archive", response_model=FormResponse)
def archive_form(
    workspace_id: UUID,
    form_id: UUID,
    service: Annotated[FormService, Depends(get_form_service)],
    db: Annotated[Session, Depends(get_db_with_rls_context)],
) -> FormResponse:
    """Archive a form."""
    command = ArchiveFormCommand(form_id=form_id)
    try:
        form = service.archive(command)
        from app.core.db.models import Form as FormModel

        db_form = db.query(FormModel).filter(FormModel.id == form.id).first()
        return FormResponse(
            id=db_form.id,
            workspace_id=db_form.workspace_id,
            folder_id=db_form.folder_id,
            name=db_form.name,
            status=db_form.status,
            draft_version_id=db_form.draft_version_id,
            published_version_id=db_form.published_version_id,
            created_by=db_form.created_by,
            created_at=db_form.created_at,
        )
    except (NotFoundError, ValidationError) as e:
        raise e


@router.post("/{form_id}/unpublish", response_model=FormResponse)
def unpublish_form(
    workspace_id: UUID,
    form_id: UUID,
    service: Annotated[FormService, Depends(get_form_service)],
    db: Annotated[Session, Depends(get_db_with_rls_context)],
) -> FormResponse:
    """Unpublish a form."""
    command = UnpublishFormCommand(form_id=form_id)
    try:
        form = service.unpublish(command)
        from app.core.db.models import Form as FormModel

        db_form = db.query(FormModel).filter(FormModel.id == form.id).first()
        return FormResponse(
            id=db_form.id,
            workspace_id=db_form.workspace_id,
            folder_id=db_form.folder_id,
            name=db_form.name,
            status=db_form.status,
            draft_version_id=db_form.draft_version_id,
            published_version_id=db_form.published_version_id,
            created_by=db_form.created_by,
            created_at=db_form.created_at,
        )
    except (NotFoundError, ValidationError) as e:
        raise e


@router.put("/{form_id}/definition", response_model=FormVersionResponse)
def update_form_definition(
    workspace_id: UUID,
    form_id: UUID,
    request: FormDefinitionUpdate,
    service: Annotated[FormService, Depends(get_form_service)],
    db: Annotated[Session, Depends(get_db_with_rls_context)],
) -> FormVersionResponse:
    """Update form draft definition."""
    command = UpdateFormDefinitionCommand(
        form_id=form_id, definition=request.definition
    )
    try:
        version = service.update_definition(command)
        from app.core.db.models import FormVersion as FormVersionModel

        db_version = (
            db.query(FormVersionModel).filter(FormVersionModel.id == version.id).first()
        )
        return FormVersionResponse(
            id=db_version.id,
            form_id=db_version.form_id,
            version_number=db_version.version_number,
            state=db_version.state,
            definition_jsonb=db_version.definition_jsonb,
            created_by=db_version.created_by,
            created_at=db_version.created_at,
        )
    except (NotFoundError, ValidationError) as e:
        raise e


@router.patch("/{form_id}/move", response_model=FormResponse)
def move_form_to_folder(
    workspace_id: UUID,
    form_id: UUID,
    request: FormMoveRequest,
    service: Annotated[FormService, Depends(get_form_service)],
    db: Annotated[Session, Depends(get_db_with_rls_context)],
) -> FormResponse:
    """Move form to a folder."""
    command = MoveFormToFolderCommand(form_id=form_id, folder_id=request.folder_id)
    try:
        form = service.move_to_folder(command)
        from app.core.db.models import Form as FormModel

        db_form = db.query(FormModel).filter(FormModel.id == form.id).first()
        return FormResponse(
            id=db_form.id,
            workspace_id=db_form.workspace_id,
            folder_id=db_form.folder_id,
            name=db_form.name,
            status=db_form.status,
            draft_version_id=db_form.draft_version_id,
            published_version_id=db_form.published_version_id,
            created_by=db_form.created_by,
            created_at=db_form.created_at,
        )
    except NotFoundError as e:
        raise e


@router.get("/{form_id}/versions", response_model=list[FormVersionResponse])
def list_form_versions(
    workspace_id: UUID,
    form_id: UUID,
    service: Annotated[FormService, Depends(get_form_service)],
    db: Annotated[Session, Depends(get_db_with_rls_context)],
) -> list[FormVersionResponse]:
    """List all versions for a form."""
    try:
        versions = service.list_versions(form_id)
        from app.core.db.models import FormVersion as FormVersionModel

        db_versions = (
            db.query(FormVersionModel)
            .filter(FormVersionModel.id.in_([v.id for v in versions]))
            .all()
        )
        return [
            FormVersionResponse(
                id=v.id,
                form_id=v.form_id,
                version_number=v.version_number,
                state=v.state,
                definition_jsonb=v.definition_jsonb,
                created_by=v.created_by,
                created_at=v.created_at,
            )
            for v in db_versions
        ]
    except NotFoundError as e:
        raise e


@router.get("/{form_id}/versions/{version_id}", response_model=FormVersionResponse)
def get_form_version(
    workspace_id: UUID,
    form_id: UUID,
    version_id: UUID,
    service: Annotated[FormService, Depends(get_form_service)],
    db: Annotated[Session, Depends(get_db_with_rls_context)],
) -> FormVersionResponse:
    """Get a specific form version."""
    try:
        version = service.get_version(version_id)
        from app.core.db.models import FormVersion as FormVersionModel

        db_version = (
            db.query(FormVersionModel).filter(FormVersionModel.id == version.id).first()
        )
        return FormVersionResponse(
            id=db_version.id,
            form_id=db_version.form_id,
            version_number=db_version.version_number,
            state=db_version.state,
            definition_jsonb=db_version.definition_jsonb,
            created_by=db_version.created_by,
            created_at=db_version.created_at,
        )
    except NotFoundError as e:
        raise e


@router.get(
    "/{form_id}/versions/{version_id}/fields", response_model=list[FormFieldResponse]
)
def get_form_version_fields(
    workspace_id: UUID,
    form_id: UUID,
    version_id: UUID,
    service: Annotated[FormService, Depends(get_form_service)],
    db: Annotated[Session, Depends(get_db_with_rls_context)],
) -> list[FormFieldResponse]:
    """Get fields for a form version."""
    try:
        fields = service.get_version_fields(version_id)
        from app.core.db.models import FormField as FormFieldModel

        db_fields = (
            db.query(FormFieldModel)
            .filter(FormFieldModel.id.in_([f.id for f in fields]))
            .order_by(FormFieldModel.order)
            .all()
        )
        return [
            FormFieldResponse(
                id=f.id,
                version_id=f.version_id,
                ref=f.ref,
                type=f.type,
                title=f.title,
                required=f.required,
                config=f.config,
                order=f.order,
            )
            for f in db_fields
        ]
    except NotFoundError as e:
        raise e


@router.post("/{form_id}/duplicate", response_model=FormResponse)
def duplicate_form(
    workspace_id: UUID,
    form_id: UUID,
    request: FormDuplicateRequest,
    identity: Annotated[Identity, Depends(get_current_user)],
    service: Annotated[FormService, Depends(get_form_service)],
    db: Annotated[Session, Depends(get_db_with_rls_context)],
) -> FormResponse:
    """Duplicate a form."""
    command = DuplicateFormCommand(
        form_id=form_id,
        new_name=request.new_name,
        created_by=identity.user_id,
    )
    try:
        form = service.duplicate(command)
        from app.core.db.models import Form as FormModel

        db_form = db.query(FormModel).filter(FormModel.id == form.id).first()
        return FormResponse(
            id=db_form.id,
            workspace_id=db_form.workspace_id,
            folder_id=db_form.folder_id,
            name=db_form.name,
            status=db_form.status,
            draft_version_id=db_form.draft_version_id,
            published_version_id=db_form.published_version_id,
            created_by=db_form.created_by,
            created_at=db_form.created_at,
        )
    except NotFoundError as e:
        raise e
