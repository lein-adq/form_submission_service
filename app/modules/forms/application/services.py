"""Forms application services."""

from uuid import UUID

from app.core.domain.value_objects import FormStatus
from app.core.exceptions import NotFoundError, ValidationError
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
from app.core.domain.value_objects import VersionState
from app.modules.forms.domain.entities import (
    Form,
    FormField,
    FormFieldChoice,
    FormVersion,
)
from app.modules.forms.domain.policies import can_archive_form, can_publish_form
from app.modules.forms.domain.repositories import (
    FormFieldChoiceRepository,
    FormFieldRepository,
    FormRepository,
    FormVersionRepository,
)


class FormService:
    """Service for form operations."""

    def __init__(
        self,
        form_repository: FormRepository,
        version_repository: FormVersionRepository,
        field_repository: FormFieldRepository,
        choice_repository: FormFieldChoiceRepository,
    ) -> None:
        self.form_repository = form_repository
        self.version_repository = version_repository
        self.field_repository = field_repository
        self.choice_repository = choice_repository

    def create(self, command: CreateFormCommand) -> Form:
        """Create a new form with an initial draft version."""
        form = Form(
            id=UUID(int=0),  # Will be set by repository
            workspace_id=command.workspace_id,
            name=command.name,
            status=FormStatus.DRAFT,
            created_by=command.created_by,
        )
        created_form = self.form_repository.create(form)

        # Create initial draft version
        draft_version = FormVersion(
            id=UUID(int=0),  # Will be set by repository
            form_id=created_form.id,
            version_number=1,
            state=VersionState.DRAFT,
            definition_jsonb={},
            created_by=command.created_by,
        )
        created_version = self.version_repository.create(draft_version)

        # Update form with draft_version_id
        created_form.draft_version_id = created_version.id
        return self.form_repository.update(created_form)

    def get_by_id(self, form_id: UUID) -> Form:
        """Get form by ID."""
        form = self.form_repository.get_by_id(form_id)
        if not form:
            raise NotFoundError("Form not found")
        return form

    def list_by_workspace(self, workspace_id: UUID) -> list[Form]:
        """List forms for a workspace."""
        return self.form_repository.list_by_workspace(workspace_id)

    def update(self, command: UpdateFormCommand) -> Form:
        """Update a form."""
        form = self.form_repository.get_by_id(command.form_id)
        if not form:
            raise NotFoundError("Form not found")

        updated_form = Form(
            id=form.id,
            workspace_id=form.workspace_id,
            name=command.name,
            status=form.status,
            created_by=form.created_by,
        )
        return self.form_repository.update(updated_form)

    def publish(self, command: PublishFormCommand) -> Form:
        """Publish a form by creating a published version from the draft."""
        form = self.form_repository.get_by_id(command.form_id)
        if not form:
            raise NotFoundError("Form not found")

        if not can_publish_form(form):
            raise ValidationError("Form cannot be published in its current state")

        # Get the draft version
        draft_version = self.version_repository.get_draft(command.form_id)
        if not draft_version:
            raise ValidationError("Form has no draft version to publish")

        # Create a new published version from the draft
        published_version = FormVersion(
            id=UUID(int=0),  # Will be set by repository
            form_id=form.id,
            version_number=draft_version.version_number + 1,
            state=VersionState.PUBLISHED,
            definition_jsonb=draft_version.definition_jsonb,
            created_by=form.created_by,
        )
        created_published = self.version_repository.create(published_version)

        # Extract fields from definition and create form_fields
        fields = self._extract_fields_from_definition(
            created_published.id, created_published.definition_jsonb
        )
        if fields:
            self.field_repository.create_bulk(fields)

        # Update form with published_version_id and status
        form.published_version_id = created_published.id
        form.status = FormStatus.PUBLISHED
        return self.form_repository.update(form)

    def _extract_fields_from_definition(
        self, version_id: UUID, definition: dict
    ) -> list[FormField]:
        """Extract form fields from definition JSONB."""
        fields = []
        field_definitions = definition.get("fields", [])

        for idx, field_def in enumerate(field_definitions):
            from app.core.domain.value_objects import FieldType

            # Map field type string to FieldType enum
            field_type_str = field_def.get("type", "short_text")
            try:
                field_type = FieldType(field_type_str)
            except ValueError:
                field_type = FieldType.SHORT_TEXT

            field = FormField(
                id=UUID(int=0),  # Will be set by repository
                version_id=version_id,
                ref=field_def.get("ref", f"field_{idx}"),
                type=field_type,
                title=field_def.get("title", ""),
                required=field_def.get("required", False),
                config=field_def.get("validations"),
                order=idx,
            )
            fields.append(field)

        return fields

    def unpublish(self, command: UnpublishFormCommand) -> Form:
        """Unpublish a form."""
        form = self.form_repository.get_by_id(command.form_id)
        if not form:
            raise NotFoundError("Form not found")

        if form.status != FormStatus.PUBLISHED:
            raise ValidationError("Form is not published")

        updated_form = Form(
            id=form.id,
            workspace_id=form.workspace_id,
            name=form.name,
            status=FormStatus.DRAFT,
            created_by=form.created_by,
        )
        return self.form_repository.update(updated_form)

    def archive(self, command: ArchiveFormCommand) -> Form:
        """Archive a form."""
        form = self.form_repository.get_by_id(command.form_id)
        if not form:
            raise NotFoundError("Form not found")

        if not can_archive_form(form):
            raise ValidationError("Form cannot be archived in its current state")

        return self.form_repository.archive(command.form_id)

    def update_definition(self, command: UpdateFormDefinitionCommand) -> FormVersion:
        """Update the draft version's definition."""
        form = self.form_repository.get_by_id(command.form_id)
        if not form:
            raise NotFoundError("Form not found")

        if form.status == FormStatus.ARCHIVED:
            raise ValidationError("Cannot update archived form")

        # Get the draft version
        draft_version = self.version_repository.get_draft(command.form_id)
        if not draft_version:
            raise ValidationError("Form has no draft version")

        # Update the draft version's definition
        draft_version.definition_jsonb = command.definition
        return self.version_repository.update(draft_version)

    def move_to_folder(self, command: MoveFormToFolderCommand) -> Form:
        """Move a form to a folder."""
        form = self.form_repository.get_by_id(command.form_id)
        if not form:
            raise NotFoundError("Form not found")

        return self.form_repository.move_to_folder(command.form_id, command.folder_id)

    def list_by_folder(self, folder_id: UUID) -> list[Form]:
        """List forms in a folder."""
        return self.form_repository.list_by_folder(folder_id)

    def get_version(self, version_id: UUID) -> FormVersion:
        """Get a form version by ID."""
        version = self.version_repository.get_by_id(version_id)
        if not version:
            raise NotFoundError("Form version not found")
        return version

    def list_versions(self, form_id: UUID) -> list[FormVersion]:
        """List all versions for a form."""
        form = self.form_repository.get_by_id(form_id)
        if not form:
            raise NotFoundError("Form not found")
        return self.version_repository.list_by_form(form_id)

    def get_version_fields(self, version_id: UUID) -> list[FormField]:
        """Get fields for a form version."""
        version = self.version_repository.get_by_id(version_id)
        if not version:
            raise NotFoundError("Form version not found")
        return self.field_repository.list_by_version(version_id)

    def get_field_choices(self, field_id: UUID) -> list[FormFieldChoice]:
        """Get choices for a form field."""
        return self.choice_repository.list_by_field(field_id)

    def duplicate(self, command: DuplicateFormCommand) -> Form:
        """Duplicate a form with its definition."""
        original_form = self.form_repository.get_by_id(command.form_id)
        if not original_form:
            raise NotFoundError("Form not found")

        # Get the draft version to copy the definition
        draft_version = self.version_repository.get_draft(command.form_id)
        definition = draft_version.definition_jsonb if draft_version else {}

        # Create new form
        new_form = Form(
            id=UUID(int=0),
            workspace_id=original_form.workspace_id,
            name=command.new_name,
            status=FormStatus.DRAFT,
            folder_id=original_form.folder_id,
            created_by=command.created_by,
        )
        created_form = self.form_repository.create(new_form)

        # Create draft version with copied definition
        new_version = FormVersion(
            id=UUID(int=0),
            form_id=created_form.id,
            version_number=1,
            state=VersionState.DRAFT,
            definition_jsonb=definition,
            created_by=command.created_by,
        )
        created_version = self.version_repository.create(new_version)

        # Update form with draft_version_id
        created_form.draft_version_id = created_version.id
        return self.form_repository.update(created_form)
