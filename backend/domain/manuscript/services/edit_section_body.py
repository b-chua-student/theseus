from domain.manuscript.infrastructure.ports.manuscript_repository import ManuscriptRepository
from domain.manuscript.models.value_objects import ManuscriptId, SectionId
from domain.src_lib.infrastructure.ports.event_publisher import EventPublisher


class EditSectionBodyService:
    """Use case: replace a section's body and publish the resulting domain events."""

    def __init__(self, repository: ManuscriptRepository, publisher: EventPublisher) -> None:
        self._repository = repository
        self._publisher = publisher

    def execute(self, manuscript_id: str, section_id: str, body: str) -> None:
        """Save the new body and publish events; do nothing if the manuscript is missing."""
        valid_manuscript_id = ManuscriptId.from_str(manuscript_id)
        valid_section_id = SectionId.from_str(section_id)

        manuscript = self._repository.get_by_id(valid_manuscript_id)

        if manuscript is not None:
            manuscript.edit_section_body(valid_section_id, body)
            self._repository.save(manuscript)
            self._publisher.publish(manuscript.pull_events())
