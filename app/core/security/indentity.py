from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Identity:
    user_id: UUID
    email: str
