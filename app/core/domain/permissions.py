from enum import Enum


class Role(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


ROLE_RANK = {
    Role.VIEWER: 10,
    Role.EDITOR: 20,
    Role.ADMIN: 30,
    Role.OWNER: 40,
}


def can(role: Role, required: Role) -> bool:
    return ROLE_RANK[role] >= ROLE_RANK[required]
