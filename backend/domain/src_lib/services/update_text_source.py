from uuid import UUID

from domain.src_lib.infrastructure.ports.event_publisher import EventPublisher
from domain.src_lib.infrastructure.ports.source_repository import SourceRepository
from domain.src_lib.models.value_objects import (
    ContentType,
    Description,
    SourceId,
    SourceTitle,
    Tags,
    TextBody,
)
from domain.src_lib.services.errors import SourceNotFound


class UpdateTextSourceService:
    """Use case: update an existing text source."""

    def __init__(self, repository: SourceRepository, publisher: EventPublisher) -> None:
        self._repository = repository
        self._publisher = publisher

    def execute(
        self,
        source_id: str,
        title: str,
        content: str,
        description: str | None = None,
        tags: list[str] | None = None,
        content_type: str = "other",
        project_id: UUID | None = None,
    ) -> None:
        """Update a text source's fields and publish update events.

        Nothing is persisted or published if validation fails.

        Raises:
            SourceNotFound: if no active text source matches (and, when given,
                belongs to `project_id`).
        """
        source = self._repository.get(SourceId.from_str(source_id))
        if (
            source is None
            or source.is_removed
            or source.kind != "text"
            or (project_id is not None and source.project_id != project_id)
        ):
            raise SourceNotFound(source_id)

        valid_title = SourceTitle(title)
        valid_content = TextBody(content)
        valid_description = Description.create(description)
        valid_tags = Tags.create(tags)
        valid_content_type = ContentType.from_str(content_type)

        source.update_text(
            title=valid_title,
            content=valid_content,
            description=valid_description,
            tags=valid_tags,
            content_type=valid_content_type,
        )
        self._repository.save(source)
        self._publisher.publish(source.pull_events())
