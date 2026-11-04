import logging
from collections import defaultdict
from collections.abc import Callable, Iterable

from domain.src_lib.infrastructure.ports.event_publisher import EventPublisher

logger = logging.getLogger(__name__)


class InProcessEventBus(EventPublisher):
    """Synchronous in-process event bus that dispatches events to subscribed handlers."""

    def __init__(self) -> None:
        self._handlers: dict[type, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: Callable) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, events: Iterable[object]) -> None:
        for event in events:
            for handler in self._handlers.get(type(event), []):
                try:
                    handler(event)
                except Exception:
                    logger.exception("Handler %s failed for %s", handler, type(event).__name__)
