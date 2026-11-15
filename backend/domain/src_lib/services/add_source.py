from uuid import UUID

from domain.src_lib.infrastructure.ports.event_publisher import EventPublisher
from domain.src_lib.infrastructure.ports.source_repository import SourceRepository
from domain.src_lib.models.aggregates import Source
from domain.src_lib.models.value_objects import Author, SourceId, SourceTitle


class AddSourceService:
    """Use case: add a new source to a project."""

    def __init__(self, repository: SourceRepository, publisher: EventPublisher) -> None:
        self._repository = repository
        self._publisher = publisher

    def execute(
        self,
        title: str,
        authors: list[str] | None,
        year: int | None,
        file_ref: str,
        project_id: UUID,
    ) -> SourceId:
        """Create and persist a source, publish its events, and return its ID."""
        valid_title = SourceTitle(title)
        valid_authors = [Author(a) for a in authors] if authors is not None else []

        source = Source.add(
            title=valid_title,
            authors=valid_authors,
            year=year,
            file_ref=file_ref,
            project_id=project_id,
        )

        self._repository.save(source)
        self._publisher.publish(source.pull_events())
        return source.id
