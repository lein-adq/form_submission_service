"""PostgreSQL implementation of form repositories."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.db.models import Form as FormModel
from app.core.db.models import FormField as FormFieldModel
from app.core.db.models import FormFieldChoice as FormFieldChoiceModel
from app.core.db.models import FormVersion as FormVersionModel
from app.core.domain.value_objects import FormStatus
from app.modules.forms.domain.entities import (
    Form,
    FormField,
    FormFieldChoice,
    FormVersion,
)
from app.modules.forms.domain.repositories import (
    FormFieldChoiceRepository,
    FormFieldRepository,
    FormRepository,
    FormVersionRepository,
)


def _form_model_to_entity(db_form: FormModel) -> Form:
    """Convert Form model to domain entity."""
    return Form(
        id=db_form.id,
        workspace_id=db_form.workspace_id,
        name=db_form.name,
        status=db_form.status,
        folder_id=db_form.folder_id,
        draft_version_id=db_form.draft_version_id,
        published_version_id=db_form.published_version_id,
        created_by=db_form.created_by,
        created_at=db_form.created_at,
    )


def _form_version_model_to_entity(db_version: FormVersionModel) -> FormVersion:
    """Convert FormVersion model to domain entity."""
    return FormVersion(
        id=db_version.id,
        form_id=db_version.form_id,
        version_number=db_version.version_number,
        state=db_version.state,
        definition_jsonb=db_version.definition_jsonb,
        created_by=db_version.created_by,
        created_at=db_version.created_at,
    )


def _form_field_model_to_entity(db_field: FormFieldModel) -> FormField:
    """Convert FormField model to domain entity."""
    return FormField(
        id=db_field.id,
        version_id=db_field.version_id,
        ref=db_field.ref,
        type=db_field.type,
        title=db_field.title,
        required=db_field.required,
        config=db_field.config,
        order=db_field.order,
    )


def _form_field_choice_model_to_entity(
    db_choice: FormFieldChoiceModel,
) -> FormFieldChoice:
    """Convert FormFieldChoice model to domain entity."""
    return FormFieldChoice(
        id=db_choice.id,
        field_id=db_choice.field_id,
        choice_id=db_choice.choice_id,
        label=db_choice.label,
        order=db_choice.order,
    )


class PostgreSQLFormRepository(FormRepository):
    """PostgreSQL implementation of FormRepository."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, form: Form) -> Form:
        """Create a new form."""
        db_form = FormModel(
            workspace_id=form.workspace_id,
            name=form.name,
            status=form.status,
            folder_id=form.folder_id,
            created_by=form.created_by,
        )
        self.db.add(db_form)
        self.db.commit()
        self.db.refresh(db_form)
        return _form_model_to_entity(db_form)

    def get_by_id(self, form_id: UUID) -> Form | None:
        """Get form by ID."""
        db_form = self.db.query(FormModel).filter(FormModel.id == form_id).first()
        if not db_form:
            return None
        return _form_model_to_entity(db_form)

    def list_by_workspace(self, workspace_id: UUID) -> list[Form]:
        """List forms for a workspace."""
        db_forms = (
            self.db.query(FormModel)
            .filter(FormModel.workspace_id == workspace_id)
            .all()
        )
        return [_form_model_to_entity(f) for f in db_forms]

    def list_by_folder(self, folder_id: UUID) -> list[Form]:
        """List forms in a folder."""
        db_forms = (
            self.db.query(FormModel).filter(FormModel.folder_id == folder_id).all()
        )
        return [_form_model_to_entity(f) for f in db_forms]

    def update(self, form: Form) -> Form:
        """Update a form."""
        db_form = self.db.query(FormModel).filter(FormModel.id == form.id).first()
        if not db_form:
            raise ValueError("Form not found")
        db_form.name = form.name
        db_form.status = form.status
        db_form.folder_id = form.folder_id
        db_form.draft_version_id = form.draft_version_id
        db_form.published_version_id = form.published_version_id
        self.db.commit()
        self.db.refresh(db_form)
        return _form_model_to_entity(db_form)

    def archive(self, form_id: UUID) -> Form:
        """Archive a form."""
        db_form = self.db.query(FormModel).filter(FormModel.id == form_id).first()
        if not db_form:
            raise ValueError("Form not found")
        db_form.status = FormStatus.ARCHIVED
        self.db.commit()
        self.db.refresh(db_form)
        return _form_model_to_entity(db_form)

    def move_to_folder(self, form_id: UUID, folder_id: UUID | None) -> Form:
        """Move form to a folder."""
        db_form = self.db.query(FormModel).filter(FormModel.id == form_id).first()
        if not db_form:
            raise ValueError("Form not found")
        db_form.folder_id = folder_id
        self.db.commit()
        self.db.refresh(db_form)
        return _form_model_to_entity(db_form)


class PostgreSQLFormVersionRepository(FormVersionRepository):
    """PostgreSQL implementation of FormVersionRepository."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, version: FormVersion) -> FormVersion:
        """Create a new form version."""
        db_version = FormVersionModel(
            form_id=version.form_id,
            version_number=version.version_number,
            state=version.state,
            definition_jsonb=version.definition_jsonb,
            created_by=version.created_by,
        )
        self.db.add(db_version)
        self.db.commit()
        self.db.refresh(db_version)
        return _form_version_model_to_entity(db_version)

    def get_by_id(self, version_id: UUID) -> FormVersion | None:
        """Get version by ID."""
        db_version = (
            self.db.query(FormVersionModel)
            .filter(FormVersionModel.id == version_id)
            .first()
        )
        if not db_version:
            return None
        return _form_version_model_to_entity(db_version)

    def list_by_form(self, form_id: UUID) -> list[FormVersion]:
        """List versions for a form."""
        db_versions = (
            self.db.query(FormVersionModel)
            .filter(FormVersionModel.form_id == form_id)
            .order_by(FormVersionModel.version_number.desc())
            .all()
        )
        return [_form_version_model_to_entity(v) for v in db_versions]

    def get_published(self, form_id: UUID) -> FormVersion | None:
        """Get the published version for a form."""
        from app.core.domain.value_objects import VersionState

        db_version = (
            self.db.query(FormVersionModel)
            .filter(
                FormVersionModel.form_id == form_id,
                FormVersionModel.state == VersionState.PUBLISHED,
            )
            .first()
        )
        if not db_version:
            return None
        return _form_version_model_to_entity(db_version)

    def get_draft(self, form_id: UUID) -> FormVersion | None:
        """Get the draft version for a form."""
        from app.core.domain.value_objects import VersionState

        db_version = (
            self.db.query(FormVersionModel)
            .filter(
                FormVersionModel.form_id == form_id,
                FormVersionModel.state == VersionState.DRAFT,
            )
            .first()
        )
        if not db_version:
            return None
        return _form_version_model_to_entity(db_version)

    def update(self, version: FormVersion) -> FormVersion:
        """Update a form version."""
        db_version = (
            self.db.query(FormVersionModel)
            .filter(FormVersionModel.id == version.id)
            .first()
        )
        if not db_version:
            raise ValueError("Form version not found")
        db_version.definition_jsonb = version.definition_jsonb
        db_version.state = version.state
        self.db.commit()
        self.db.refresh(db_version)
        return _form_version_model_to_entity(db_version)


class PostgreSQLFormFieldRepository(FormFieldRepository):
    """PostgreSQL implementation of FormFieldRepository."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_bulk(self, fields: list[FormField]) -> list[FormField]:
        """Create multiple fields for a version."""
        db_fields = [
            FormFieldModel(
                version_id=f.version_id,
                ref=f.ref,
                type=f.type,
                title=f.title,
                required=f.required,
                config=f.config,
                order=f.order,
            )
            for f in fields
        ]
        self.db.add_all(db_fields)
        self.db.commit()
        for db_field in db_fields:
            self.db.refresh(db_field)
        return [_form_field_model_to_entity(f) for f in db_fields]

    def list_by_version(self, version_id: UUID) -> list[FormField]:
        """List fields for a version."""
        db_fields = (
            self.db.query(FormFieldModel)
            .filter(FormFieldModel.version_id == version_id)
            .order_by(FormFieldModel.order)
            .all()
        )
        return [_form_field_model_to_entity(f) for f in db_fields]

    def get_by_ref(self, version_id: UUID, ref: str) -> FormField | None:
        """Get field by version and ref."""
        db_field = (
            self.db.query(FormFieldModel)
            .filter(
                FormFieldModel.version_id == version_id,
                FormFieldModel.ref == ref,
            )
            .first()
        )
        if not db_field:
            return None
        return _form_field_model_to_entity(db_field)


class PostgreSQLFormFieldChoiceRepository(FormFieldChoiceRepository):
    """PostgreSQL implementation of FormFieldChoiceRepository."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_bulk(self, choices: list[FormFieldChoice]) -> list[FormFieldChoice]:
        """Create multiple choices for a field."""
        db_choices = [
            FormFieldChoiceModel(
                field_id=c.field_id,
                choice_id=c.choice_id,
                label=c.label,
                order=c.order,
            )
            for c in choices
        ]
        self.db.add_all(db_choices)
        self.db.commit()
        for db_choice in db_choices:
            self.db.refresh(db_choice)
        return [_form_field_choice_model_to_entity(c) for c in db_choices]

    def list_by_field(self, field_id: UUID) -> list[FormFieldChoice]:
        """List choices for a field."""
        db_choices = (
            self.db.query(FormFieldChoiceModel)
            .filter(FormFieldChoiceModel.field_id == field_id)
            .order_by(FormFieldChoiceModel.order)
            .all()
        )
        return [_form_field_choice_model_to_entity(c) for c in db_choices]
