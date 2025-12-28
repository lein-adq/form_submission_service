"""Workspaces API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.core.dependencies import get_db_with_rls_context, get_current_user
from app.core.exceptions import ConflictError, NotFoundError
from app.core.security.indentity import Identity
from app.modules.workspaces.api.schemas import (
    AddMemberRequest,
    FolderCreate,
    FolderMove,
    FolderResponse,
    FolderUpdate,
    MembershipResponse,
    UpdateMemberRoleRequest,
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.modules.workspaces.application.commands import (
    AddMemberCommand,
    CreateFolderCommand,
    CreateWorkspaceCommand,
    DeleteFolderCommand,
    DeleteWorkspaceCommand,
    MoveFolderCommand,
    RemoveMemberCommand,
    UpdateFolderCommand,
    UpdateMemberRoleCommand,
    UpdateWorkspaceCommand,
)
from app.modules.workspaces.application.services import (
    FolderService,
    MembershipService,
    WorkspaceService,
)
from app.modules.workspaces.infrastructure.repository_pg import (
    PostgreSQLFolderRepository,
    PostgreSQLMembershipRepository,
    PostgreSQLWorkspaceRepository,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def get_workspace_service(db: Annotated[Session, Depends(get_db)]) -> WorkspaceService:
    """Dependency for workspace service."""
    workspace_repo = PostgreSQLWorkspaceRepository(db)
    membership_repo = PostgreSQLMembershipRepository(db)
    return WorkspaceService(workspace_repo, membership_repo)


def get_membership_service(
    db: Annotated[Session, Depends(get_db)],
) -> MembershipService:
    """Dependency for membership service."""
    workspace_repo = PostgreSQLWorkspaceRepository(db)
    membership_repo = PostgreSQLMembershipRepository(db)
    return MembershipService(workspace_repo, membership_repo)


def get_folder_service(
    db: Annotated[Session, Depends(get_db)],
) -> FolderService:
    """Dependency for folder service."""
    folder_repo = PostgreSQLFolderRepository(db)
    workspace_repo = PostgreSQLWorkspaceRepository(db)
    return FolderService(folder_repo, workspace_repo)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=WorkspaceResponse)
def create_workspace(
    request: WorkspaceCreate,
    identity: Annotated[Identity, Depends(get_current_user)],
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
    db: Annotated[Session, Depends(get_db)],
) -> WorkspaceResponse:
    """Create a new workspace."""
    command = CreateWorkspaceCommand(
        name=request.name, creator_user_id=identity.user_id
    )
    workspace = service.create(command)
    # Fetch full workspace with created_at
    from app.core.db.models import Workspace as WorkspaceModel

    db_workspace = (
        db.query(WorkspaceModel).filter(WorkspaceModel.id == workspace.id).first()
    )
    return WorkspaceResponse(
        id=db_workspace.id,
        name=db_workspace.name,
        created_at=db_workspace.created_at,
    )


@router.get("", response_model=list[WorkspaceResponse])
def list_workspaces(
    identity: Annotated[Identity, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_with_rls_context)],
) -> list[WorkspaceResponse]:
    """List user's workspaces."""
    from app.core.db.models import Workspace as WorkspaceModel
    from app.core.db.models import WorkspaceMember as WorkspaceMemberModel

    workspaces = (
        db.query(WorkspaceModel)
        .join(WorkspaceMemberModel)
        .filter(WorkspaceMemberModel.user_id == identity.user_id)
        .all()
    )
    return [
        WorkspaceResponse(id=w.id, name=w.name, created_at=w.created_at)
        for w in workspaces
    ]


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: UUID,
    db: Annotated[Session, Depends(get_db_with_rls_context)],
) -> WorkspaceResponse:
    """Get workspace details."""
    from app.core.db.models import Workspace as WorkspaceModel

    workspace = (
        db.query(WorkspaceModel).filter(WorkspaceModel.id == workspace_id).first()
    )
    if not workspace:
        raise NotFoundError("Workspace not found")
    return WorkspaceResponse(
        id=workspace.id, name=workspace.name, created_at=workspace.created_at
    )


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace(
    workspace_id: UUID,
    request: WorkspaceUpdate,
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
    db: Annotated[Session, Depends(get_db)],
) -> WorkspaceResponse:
    """Update a workspace."""
    command = UpdateWorkspaceCommand(workspace_id=workspace_id, name=request.name)
    try:
        workspace = service.update(command)
        # Fetch full workspace with created_at
        from app.core.db.models import Workspace as WorkspaceModel

        db_workspace = (
            db.query(WorkspaceModel).filter(WorkspaceModel.id == workspace.id).first()
        )
        return WorkspaceResponse(
            id=db_workspace.id,
            name=db_workspace.name,
            created_at=db_workspace.created_at,
        )
    except NotFoundError as e:
        raise e


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace_id: UUID,
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
    db: Annotated[Session, Depends(get_db_with_rls_context)],
) -> None:
    """Delete a workspace."""
    command = DeleteWorkspaceCommand(workspace_id=workspace_id)
    try:
        service.delete(command)
    except NotFoundError as e:
        raise e


@router.get("/{workspace_id}/members", response_model=list[MembershipResponse])
def list_members(
    workspace_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> list[MembershipResponse]:
    """List all members of a workspace."""
    from app.core.db.models import WorkspaceMember as WorkspaceMemberModel

    db_memberships = (
        db.query(WorkspaceMemberModel)
        .filter(WorkspaceMemberModel.workspace_id == workspace_id)
        .all()
    )
    return [
        MembershipResponse(
            workspace_id=m.workspace_id,
            user_id=m.user_id,
            role=m.role,
            created_at=m.created_at,
        )
        for m in db_memberships
    ]


@router.post(
    "/{workspace_id}/members",
    status_code=status.HTTP_201_CREATED,
    response_model=MembershipResponse,
)
def add_member(
    workspace_id: UUID,
    request: AddMemberRequest,
    service: Annotated[MembershipService, Depends(get_membership_service)],
    db: Annotated[Session, Depends(get_db)],
) -> MembershipResponse:
    """Add a member to a workspace."""
    command = AddMemberCommand(
        workspace_id=workspace_id,
        user_id=request.user_id,
        role=request.role,
    )
    try:
        membership = service.add_member(command)
        # Fetch full membership with created_at
        from app.core.db.models import WorkspaceMember as WorkspaceMemberModel

        db_membership = (
            db.query(WorkspaceMemberModel)
            .filter(
                WorkspaceMemberModel.workspace_id == membership.workspace_id,
                WorkspaceMemberModel.user_id == membership.user_id,
            )
            .first()
        )
        return MembershipResponse(
            workspace_id=db_membership.workspace_id,
            user_id=db_membership.user_id,
            role=db_membership.role,
            created_at=db_membership.created_at,
        )
    except (NotFoundError, ConflictError) as e:
        raise e


@router.patch("/{workspace_id}/members/{user_id}", response_model=MembershipResponse)
def update_member_role(
    workspace_id: UUID,
    user_id: UUID,
    request: UpdateMemberRoleRequest,
    service: Annotated[MembershipService, Depends(get_membership_service)],
    db: Annotated[Session, Depends(get_db)],
) -> MembershipResponse:
    """Update a member's role."""
    command = UpdateMemberRoleCommand(
        workspace_id=workspace_id,
        user_id=user_id,
        role=request.role,
    )
    try:
        membership = service.update_role(command)
        # Fetch full membership with created_at
        from app.core.db.models import WorkspaceMember as WorkspaceMemberModel

        db_membership = (
            db.query(WorkspaceMemberModel)
            .filter(
                WorkspaceMemberModel.workspace_id == membership.workspace_id,
                WorkspaceMemberModel.user_id == membership.user_id,
            )
            .first()
        )
        return MembershipResponse(
            workspace_id=db_membership.workspace_id,
            user_id=db_membership.user_id,
            role=db_membership.role,
            created_at=db_membership.created_at,
        )
    except NotFoundError as e:
        raise e


@router.delete(
    "/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_member(
    workspace_id: UUID,
    user_id: UUID,
    service: Annotated[MembershipService, Depends(get_membership_service)],
) -> None:
    """Remove a member from a workspace."""
    command = RemoveMemberCommand(workspace_id=workspace_id, user_id=user_id)
    try:
        service.remove_member(command)
    except NotFoundError as e:
        raise e


# === Folder endpoints ===


@router.post(
    "/{workspace_id}/folders",
    status_code=status.HTTP_201_CREATED,
    response_model=FolderResponse,
)
def create_folder(
    workspace_id: UUID,
    request: FolderCreate,
    service: Annotated[FolderService, Depends(get_folder_service)],
    db: Annotated[Session, Depends(get_db)],
) -> FolderResponse:
    """Create a new folder."""
    command = CreateFolderCommand(
        workspace_id=workspace_id,
        name=request.name,
        parent_id=request.parent_id,
    )
    try:
        folder = service.create(command)
        # Fetch full folder with created_at
        from app.core.db.models import Folder as FolderModel

        db_folder = db.query(FolderModel).filter(FolderModel.id == folder.id).first()
        return FolderResponse(
            id=db_folder.id,
            workspace_id=db_folder.workspace_id,
            name=db_folder.name,
            parent_id=db_folder.parent_id,
            created_at=db_folder.created_at,
        )
    except (NotFoundError, ConflictError) as e:
        raise e


@router.get("/{workspace_id}/folders", response_model=list[FolderResponse])
def list_folders(
    workspace_id: UUID,
    service: Annotated[FolderService, Depends(get_folder_service)],
    db: Annotated[Session, Depends(get_db)],
) -> list[FolderResponse]:
    """List root folders for a workspace."""
    folders = service.list_by_workspace(workspace_id)
    from app.core.db.models import Folder as FolderModel

    db_folders = (
        db.query(FolderModel).filter(FolderModel.id.in_([f.id for f in folders])).all()
    )
    return [
        FolderResponse(
            id=f.id,
            workspace_id=f.workspace_id,
            name=f.name,
            parent_id=f.parent_id,
            created_at=f.created_at,
        )
        for f in db_folders
    ]


@router.get("/folders/{folder_id}", response_model=FolderResponse)
def get_folder(
    folder_id: UUID,
    service: Annotated[FolderService, Depends(get_folder_service)],
    db: Annotated[Session, Depends(get_db)],
) -> FolderResponse:
    """Get folder details."""
    try:
        folder = service.get_by_id(folder_id)
        from app.core.db.models import Folder as FolderModel

        db_folder = db.query(FolderModel).filter(FolderModel.id == folder.id).first()
        return FolderResponse(
            id=db_folder.id,
            workspace_id=db_folder.workspace_id,
            name=db_folder.name,
            parent_id=db_folder.parent_id,
            created_at=db_folder.created_at,
        )
    except NotFoundError as e:
        raise e


@router.get("/folders/{folder_id}/children", response_model=list[FolderResponse])
def list_folder_children(
    folder_id: UUID,
    service: Annotated[FolderService, Depends(get_folder_service)],
    db: Annotated[Session, Depends(get_db)],
) -> list[FolderResponse]:
    """List child folders."""
    try:
        children = service.list_children(folder_id)
        from app.core.db.models import Folder as FolderModel

        db_folders = (
            db.query(FolderModel)
            .filter(FolderModel.id.in_([f.id for f in children]))
            .all()
        )
        return [
            FolderResponse(
                id=f.id,
                workspace_id=f.workspace_id,
                name=f.name,
                parent_id=f.parent_id,
                created_at=f.created_at,
            )
            for f in db_folders
        ]
    except NotFoundError as e:
        raise e


@router.get("/{workspace_id}/folders/{folder_id}/forms")
def list_forms_in_folder(
    workspace_id: UUID,
    folder_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> list[dict]:
    """List forms in a folder."""
    from app.core.db.models import Form as FormModel

    forms = (
        db.query(FormModel)
        .filter(
            FormModel.folder_id == folder_id, FormModel.workspace_id == workspace_id
        )
        .all()
    )
    return [
        {
            "id": f.id,
            "workspace_id": f.workspace_id,
            "folder_id": f.folder_id,
            "name": f.name,
            "status": f.status,
            "draft_version_id": f.draft_version_id,
            "published_version_id": f.published_version_id,
            "created_by": f.created_by,
            "created_at": f.created_at,
        }
        for f in forms
    ]


@router.patch("/folders/{folder_id}", response_model=FolderResponse)
def update_folder(
    folder_id: UUID,
    request: FolderUpdate,
    service: Annotated[FolderService, Depends(get_folder_service)],
    db: Annotated[Session, Depends(get_db)],
) -> FolderResponse:
    """Update a folder."""
    command = UpdateFolderCommand(folder_id=folder_id, name=request.name)
    try:
        folder = service.update(command)
        from app.core.db.models import Folder as FolderModel

        db_folder = db.query(FolderModel).filter(FolderModel.id == folder.id).first()
        return FolderResponse(
            id=db_folder.id,
            workspace_id=db_folder.workspace_id,
            name=db_folder.name,
            parent_id=db_folder.parent_id,
            created_at=db_folder.created_at,
        )
    except NotFoundError as e:
        raise e


@router.patch("/folders/{folder_id}/move", response_model=FolderResponse)
def move_folder(
    folder_id: UUID,
    request: FolderMove,
    service: Annotated[FolderService, Depends(get_folder_service)],
    db: Annotated[Session, Depends(get_db)],
) -> FolderResponse:
    """Move folder to a new parent."""
    command = MoveFolderCommand(
        folder_id=folder_id, new_parent_id=request.new_parent_id
    )
    try:
        folder = service.move(command)
        from app.core.db.models import Folder as FolderModel

        db_folder = db.query(FolderModel).filter(FolderModel.id == folder.id).first()
        return FolderResponse(
            id=db_folder.id,
            workspace_id=db_folder.workspace_id,
            name=db_folder.name,
            parent_id=db_folder.parent_id,
            created_at=db_folder.created_at,
        )
    except (NotFoundError, ConflictError) as e:
        raise e


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(
    folder_id: UUID,
    service: Annotated[FolderService, Depends(get_folder_service)],
) -> None:
    """Delete a folder."""
    command = DeleteFolderCommand(folder_id=folder_id)
    try:
        service.delete(command)
    except (NotFoundError, ConflictError) as e:
        raise e
