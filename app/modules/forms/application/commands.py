"""Forms application commands."""

from dataclasses import dataclass
from uuid import UUID

from app.core.domain.value_objects import FormStatus


@dataclass
class CreateFormCommand:
    """Command to create a form."""

    workspace_id: UUID
    name: str
    created_by: UUID


@dataclass
class UpdateFormCommand:
    """Command to update a form."""

    form_id: UUID
    name: str


@dataclass
class PublishFormCommand:
    """Command to publish a form."""

    form_id: UUID


@dataclass
class UnpublishFormCommand:
    """Command to unpublish a form."""

    form_id: UUID


@dataclass
class ArchiveFormCommand:
    """Command to archive a form."""

    form_id: UUID


@dataclass
class UpdateFormDefinitionCommand:
    """Command to update a form's draft definition."""

    form_id: UUID
    definition: dict


@dataclass
class MoveFormToFolderCommand:
    """Command to move a form to a folder."""

    form_id: UUID
    folder_id: UUID | None


@dataclass
class DuplicateFormCommand:
    """Command to duplicate a form."""

    form_id: UUID
    new_name: str
    created_by: UUID
