"""Domain events for event-driven architecture."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class DomainEvent:
    """Base class for domain events."""

    event_id: UUID
    occurred_at: datetime
    aggregate_id: UUID


@dataclass
class FormCreated(DomainEvent):
    """Event raised when a form is created."""

    form_id: UUID
    workspace_id: UUID
    created_by: UUID


@dataclass
class FormPublished(DomainEvent):
    """Event raised when a form is published."""

    form_id: UUID
    workspace_id: UUID


@dataclass
class SubmissionReceived(DomainEvent):
    """Event raised when a submission is received."""

    submission_id: UUID
    form_id: UUID


# Event bus interface (for future webhook support)
class EventBus:
    """Interface for event bus."""

    def publish(self, event: DomainEvent) -> None:
        """Publish a domain event."""
        raise NotImplementedError


class InMemoryEventBus(EventBus):
    """In-memory event bus implementation."""

    def __init__(self) -> None:
        self._subscribers: list[Callable[[DomainEvent], None]] = []

    def subscribe(self, handler: Callable[[DomainEvent], None]) -> None:
        """Subscribe to events."""
        self._subscribers.append(handler)

    def publish(self, event: DomainEvent) -> None:
        """Publish event to all subscribers."""
        for handler in self._subscribers:
            handler(event)
