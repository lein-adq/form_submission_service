"""Factory functions for creating test data."""

from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.db.models import (
    Answer,
    Folder,
    Form,
    FormField,
    FormFieldChoice,
    FormVersion,
    Submission,
    User,
    Workspace,
    WorkspaceMember,
)
from app.core.security.hashing import hash_password


def create_user(
    db: Session,
    email: str | None = None,
    password: str = "testpassword",
) -> User:
    """Create a test user."""
    if email is None:
        email = f"user-{uuid4()}@example.com"

    user = User(
        email=email,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_workspace(
    db: Session,
    name: str | None = None,
    owner_id: UUID | None = None,
) -> Workspace:
    """Create a test workspace with optional owner."""
    if name is None:
        name = f"Workspace {uuid4()}"

    workspace = Workspace(name=name)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    # Add owner as member if provided
    if owner_id:
        membership = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=owner_id,
            role="owner",
        )
        db.add(membership)
        db.commit()

    return workspace


def create_workspace_member(
    db: Session,
    workspace_id: UUID,
    user_id: UUID,
    role: str = "member",
) -> WorkspaceMember:
    """Create a workspace membership."""
    membership = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=user_id,
        role=role,
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def create_folder(
    db: Session,
    workspace_id: UUID,
    name: str | None = None,
    parent_id: UUID | None = None,
) -> Folder:
    """Create a test folder."""
    if name is None:
        name = f"Folder {uuid4()}"

    folder = Folder(
        workspace_id=workspace_id,
        name=name,
        parent_id=parent_id,
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


def create_form(
    db: Session,
    workspace_id: UUID,
    name: str | None = None,
    created_by: UUID | None = None,
    folder_id: UUID | None = None,
    status: str = "draft",
) -> Form:
    """Create a test form."""
    if name is None:
        name = f"Form {uuid4()}"

    form = Form(
        workspace_id=workspace_id,
        name=name,
        created_by=created_by,
        folder_id=folder_id,
        status=status,
    )
    db.add(form)
    db.commit()
    db.refresh(form)

    # Create draft version
    version = create_form_version(
        db=db,
        form_id=form.id,
        created_by=created_by,
        state="draft",
    )

    # Update form's draft_version_id
    form.draft_version_id = version.id
    db.commit()
    db.refresh(form)

    return form


def create_form_version(
    db: Session,
    form_id: UUID,
    created_by: UUID | None = None,
    version_number: int = 1,
    state: str = "draft",
    definition_jsonb: dict | None = None,
) -> FormVersion:
    """Create a form version."""
    if definition_jsonb is None:
        definition_jsonb = {"fields": []}

    version = FormVersion(
        form_id=form_id,
        version_number=version_number,
        state=state,
        definition_jsonb=definition_jsonb,
        created_by=created_by,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def create_form_field(
    db: Session,
    version_id: UUID,
    ref: str | None = None,
    field_type: str = "short_text",
    title: str | None = None,
    required: bool = False,
    order: int = 0,
    config: dict | None = None,
) -> FormField:
    """Create a form field."""
    if ref is None:
        ref = f"field_{uuid4().hex[:8]}"
    if title is None:
        title = f"Field {ref}"
    if config is None:
        config = {}

    field = FormField(
        version_id=version_id,
        ref=ref,
        type=field_type,
        title=title,
        required=required,
        order=order,
        config=config,
    )
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


def create_form_field_choice(
    db: Session,
    field_id: UUID,
    label: str | None = None,
    value: str | None = None,
    order: int = 0,
) -> FormFieldChoice:
    """Create a form field choice."""
    if label is None:
        label = f"Choice {uuid4().hex[:8]}"
    if value is None:
        value = label.lower().replace(" ", "_")

    choice = FormFieldChoice(
        field_id=field_id,
        label=label,
        value=value,
        order=order,
    )
    db.add(choice)
    db.commit()
    db.refresh(choice)
    return choice


def create_submission(
    db: Session,
    form_id: UUID,
    form_version_id: UUID,
    workspace_id: UUID,
    ip_address: str | None = None,
    user_agent: str | None = None,
    source: str = "web",
) -> Submission:
    """Create a submission."""
    submission = Submission(
        form_id=form_id,
        form_version_id=form_version_id,
        workspace_id=workspace_id,
        ip_address=ip_address,
        user_agent=user_agent,
        source=source,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def create_answer(
    db: Session,
    submission_id: UUID,
    field_ref: str,
    field_type: str,
    value_text: str | None = None,
    value_number: float | None = None,
    value_bool: bool | None = None,
    value_jsonb: dict | None = None,
) -> Answer:
    """Create an answer."""
    answer = Answer(
        submission_id=submission_id,
        field_ref=field_ref,
        field_type=field_type,
        value_text=value_text,
        value_number=value_number,
        value_bool=value_bool,
        value_jsonb=value_jsonb,
    )
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return answer
