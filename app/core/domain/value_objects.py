"""Value objects for domain entities."""

from enum import Enum
from uuid import UUID


class FormStatus(str, Enum):
    """Form status values."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class VersionState(str, Enum):
    """Form version state values."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class FieldType(str, Enum):
    """Form field type values."""

    SHORT_TEXT = "short_text"
    LONG_TEXT = "long_text"
    EMAIL = "email"
    NUMBER = "number"
    DATE = "date"
    MULTIPLE_CHOICE = "multiple_choice"
    CHECKBOX = "checkbox"
    DROPDOWN = "dropdown"
    FILE_UPLOAD = "file_upload"
    RATING = "rating"
    YES_NO = "yes_no"
    PHONE = "phone"
    URL = "url"


class FormId:
    """Form ID value object."""

    def __init__(self, value: UUID | str) -> None:
        self.value = UUID(str(value)) if isinstance(value, str) else value

    def __str__(self) -> str:
        return str(self.value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FormId):
            return False
        return self.value == other.value


class WorkspaceId:
    """Workspace ID value object."""

    def __init__(self, value: UUID | str) -> None:
        self.value = UUID(str(value)) if isinstance(value, str) else value

    def __str__(self) -> str:
        return str(self.value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WorkspaceId):
            return False
        return self.value == other.value


class UserId:
    """User ID value object."""

    def __init__(self, value: UUID | str) -> None:
        self.value = UUID(str(value)) if isinstance(value, str) else value

    def __str__(self) -> str:
        return str(self.value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UserId):
            return False
        return self.value == other.value


class Email:
    """Email value object with validation."""

    def __init__(self, value: str) -> None:
        if not value or "@" not in value:
            raise ValueError("Invalid email address")
        self.value = value.lower().strip()

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Email):
            return False
        return self.value == other.value
