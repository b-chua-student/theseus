from domain.src_lib.infrastructure.ports.event_publisher import EventPublisher
from domain.src_lib.infrastructure.ports.source_repository import SourceRepository
from domain.src_lib.models.value_objects import SourceId

from .errors import SourceNotFound


class RemoveSourceService:
    """Use case: remove a source and publish the resulting events."""

    def __init__(self, repository: SourceRepository, publisher: EventPublisher) -> None:
        self._repository = repository
        self._publisher = publisher

    def execute(self, source_id: str) -> None:
        """Soft-delete the source.

        Raises:
            SourceNotFound: if the source does not exist.
        """
        source = self._repository.get(SourceId.from_str(source_id))
        if source is None:
            raise SourceNotFound(source_id)
        source.remove()
        self._repository.save(source)
        self._publisher.publish(source.pull_events())
