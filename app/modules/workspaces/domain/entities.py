"""Workspaces domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.core.domain.permissions import Role


@dataclass
class Folder:
    """Folder domain entity for organizing forms."""

    id: UUID
    workspace_id: UUID
    name: str
    parent_id: UUID | None = None
    created_at: datetime | None = None
    children: list["Folder"] = field(default_factory=list)


@dataclass
class Workspace:
    """Workspace domain entity."""

    id: UUID
    name: str
    created_at: datetime | None = None
    folders: list[Folder] = field(default_factory=list)


@dataclass
class Membership:
    """Workspace membership domain entity."""

    workspace_id: UUID
    user_id: UUID
    role: Role
    created_at: datetime | None = None
