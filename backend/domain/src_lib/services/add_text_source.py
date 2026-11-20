from uuid import UUID

from domain.src_lib.infrastructure.ports.event_publisher import EventPublisher
from domain.src_lib.infrastructure.ports.source_repository import SourceRepository
from domain.src_lib.models.aggregates import Source
from domain.src_lib.models.value_objects import (
    ContentType,
    Description,
    SourceId,
    SourceTitle,
    Tags,
    TextBody,
)


class AddTextSourceService:
    """Use case: add a new text source to a project."""

    def __init__(self, repository: SourceRepository, publisher: EventPublisher) -> None:
        """Initialize the instance."""
        self._repository = repository
        self._publisher = publisher

    def execute(
        self,
        title: str,
        content: str,
        project_id: UUID,
        description: str | None = None,
        tags: list[str] | None = None,
        content_type: str = "other",
    ) -> SourceId:
        """Create and persist a text source, publish its events, and return its ID."""
        valid_title = SourceTitle(title)
        valid_content = TextBody(content)
        valid_description = Description.create(description)
        valid_tags = Tags.create(tags)
        valid_content_type = ContentType.from_str(content_type)

        source = Source.add_text(
            title=valid_title,
            content=valid_content,
            project_id=project_id,
            description=valid_description,
            tags=valid_tags,
            content_type=valid_content_type,
        )

        self._repository.save(source)
        self._publisher.publish(source.pull_events())
        return source.id
