from dataclasses import dataclass
from uuid import UUID


@dataclass
class Form:
    id: UUID
    workspace_id: UUID
    name: str
    status: str
