from domain.manuscript.infrastructure.ports.manuscript_repository import ManuscriptRepository
from domain.manuscript.models.entities import Section
from domain.manuscript.models.value_objects import Heading, ManuscriptId, SectionId
from domain.revision_history.infrastructure.ports.manuscript_writer import ManuscriptWriter
from domain.revision_history.models.aggregates import Snapshot
from domain.revision_history.services.errors import ManuscriptNotFound


class ManuscriptRepositoryWriter(ManuscriptWriter):
    """Adapts the manuscript domain's repository to the revision history writer port."""

    def __init__(self, repository: ManuscriptRepository) -> None:
        self._repository = repository

    def apply_snapshot(self, manuscript_id: str, snapshot: Snapshot) -> None:
        manuscript = self._repository.get_by_id(ManuscriptId.from_str(manuscript_id))
        if manuscript is None:
            raise ManuscriptNotFound(str(manuscript_id))

        manuscript.replace_sections(
            [
                Section(
                    id=SectionId(s.id),
                    parent_id=SectionId(s.parent_id) if s.parent_id else None,
                    heading=Heading(s.heading),
                    ordinal=s.ordinal,
                    body=s.body,
                )
                for s in snapshot.sections
            ]
        )
        self._repository.save(manuscript)
