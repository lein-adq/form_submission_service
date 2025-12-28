"""Workspaces API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.domain.permissions import Role


class WorkspaceCreate(BaseModel):
    """Request schema for creating a workspace."""

    name: str


class WorkspaceUpdate(BaseModel):
    """Request schema for updating a workspace."""

    name: str


class WorkspaceResponse(BaseModel):
    """Response schema for workspace."""

    id: UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class MembershipResponse(BaseModel):
    """Response schema for membership."""

    workspace_id: UUID
    user_id: UUID
    role: Role
    created_at: datetime

    class Config:
        from_attributes = True


class AddMemberRequest(BaseModel):
    """Request schema for adding a member."""

    user_id: UUID
    role: Role


class UpdateMemberRoleRequest(BaseModel):
    """Request schema for updating member role."""

    role: Role


class FolderCreate(BaseModel):
    """Request schema for creating a folder."""

    name: str
    parent_id: UUID | None = None


class FolderUpdate(BaseModel):
    """Request schema for updating a folder."""

    name: str


class FolderMove(BaseModel):
    """Request schema for moving a folder."""

    new_parent_id: UUID | None = None


class FolderResponse(BaseModel):
    """Response schema for folder."""

    id: UUID
    workspace_id: UUID
    name: str
    parent_id: UUID | None
    created_at: datetime

    class Config:
        from_attributes = True
