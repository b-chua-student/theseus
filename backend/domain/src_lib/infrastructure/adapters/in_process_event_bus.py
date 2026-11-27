import logging
from collections import defaultdict
from collections.abc import Callable, Iterable

from domain.src_lib.infrastructure.ports.event_publisher import EventPublisher
from domain.src_lib.models.events import SourceRemoved

logger = logging.getLogger(__name__)


class InProcessEventBus(EventPublisher):
    """Synchronous in-process event bus that dispatches events to subscribed handlers."""

    def __init__(self) -> None:
        """Initialize the instance."""
        self._handlers: dict[type, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: Callable) -> None:
        """Register an event handler."""
        self._handlers[event_type].append(handler)

    def publish(self, events: Iterable[object]) -> None:
        """Publish domain events."""
        removal_errors: list[Exception] = []
        for event in events:
            for handler in self._handlers.get(type(event), []):
                try:
                    handler(event)
                except Exception as exc:
                    if isinstance(event, SourceRemoved):
                        removal_errors.append(exc)
                    logger.exception("Handler %s failed for %s", handler, type(event).__name__)
        if removal_errors:
            raise ExceptionGroup("Source removal cleanup failed", removal_errors)
