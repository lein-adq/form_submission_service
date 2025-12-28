"""Forms domain repository interfaces."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.forms.domain.entities import (
    Form,
    FormField,
    FormFieldChoice,
    FormVersion,
)


class FormRepository(ABC):
    """Repository interface for form operations."""

    @abstractmethod
    def create(self, form: Form) -> Form:
        """Create a new form."""
        pass

    @abstractmethod
    def get_by_id(self, form_id: UUID) -> Form | None:
        """Get form by ID."""
        pass

    @abstractmethod
    def list_by_workspace(self, workspace_id: UUID) -> list[Form]:
        """List forms for a workspace."""
        pass

    @abstractmethod
    def list_by_folder(self, folder_id: UUID) -> list[Form]:
        """List forms in a folder."""
        pass

    @abstractmethod
    def update(self, form: Form) -> Form:
        """Update a form."""
        pass

    @abstractmethod
    def archive(self, form_id: UUID) -> Form:
        """Archive a form."""
        pass

    @abstractmethod
    def move_to_folder(self, form_id: UUID, folder_id: UUID | None) -> Form:
        """Move form to a folder."""
        pass


class FormVersionRepository(ABC):
    """Repository interface for form version operations."""

    @abstractmethod
    def create(self, version: FormVersion) -> FormVersion:
        """Create a new form version."""
        pass

    @abstractmethod
    def get_by_id(self, version_id: UUID) -> FormVersion | None:
        """Get version by ID."""
        pass

    @abstractmethod
    def list_by_form(self, form_id: UUID) -> list[FormVersion]:
        """List versions for a form."""
        pass

    @abstractmethod
    def get_published(self, form_id: UUID) -> FormVersion | None:
        """Get the published version for a form."""
        pass

    @abstractmethod
    def get_draft(self, form_id: UUID) -> FormVersion | None:
        """Get the draft version for a form."""
        pass

    @abstractmethod
    def update(self, version: FormVersion) -> FormVersion:
        """Update a form version."""
        pass


class FormFieldRepository(ABC):
    """Repository interface for form field operations."""

    @abstractmethod
    def create_bulk(self, fields: list[FormField]) -> list[FormField]:
        """Create multiple fields for a version."""
        pass

    @abstractmethod
    def list_by_version(self, version_id: UUID) -> list[FormField]:
        """List fields for a version."""
        pass

    @abstractmethod
    def get_by_ref(self, version_id: UUID, ref: str) -> FormField | None:
        """Get field by version and ref."""
        pass


class FormFieldChoiceRepository(ABC):
    """Repository interface for form field choice operations."""

    @abstractmethod
    def create_bulk(self, choices: list[FormFieldChoice]) -> list[FormFieldChoice]:
        """Create multiple choices for a field."""
        pass

    @abstractmethod
    def list_by_field(self, field_id: UUID) -> list[FormFieldChoice]:
        """List choices for a field."""
        pass
