from abc import ABC, abstractmethod
from collections.abc import Iterable


class EventPublisher(ABC):
    """Port for publishing domain events to interested subscribers."""

    @abstractmethod
    def publish(self, events: Iterable[object]) -> None:
        """Publish the given domain events."""
        ...
