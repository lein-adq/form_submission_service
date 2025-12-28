"""Auth domain entities."""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class User:
    """User domain entity."""

    id: UUID
    email: str
    password_hash: str
