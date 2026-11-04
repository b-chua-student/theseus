from domain.manuscript.infrastructure.ports.manuscript_repository import ManuscriptRepository
from domain.manuscript.models.value_objects import ManuscriptId
from domain.revision_history.infrastructure.ports.manuscript_reader import ManuscriptReader
from domain.revision_history.models.value_objects import SectionSnapshot, Snapshot


class ManuscriptRepositoryReader(ManuscriptReader):
    """Adapts the manuscript domain's repository to the revision history reader port."""

    def __init__(self, repository: ManuscriptRepository) -> None:
        self._repository = repository

    def get_snapshot(self, manuscript_id: str) -> Snapshot | None:
        manuscript = self._repository.get_by_id(ManuscriptId.from_str(manuscript_id))
        if manuscript is None:
            return None
        return Snapshot(
            tuple(
                SectionSnapshot(
                    id=s.id.value,
                    parent_id=s.parent_id.value if s.parent_id else None,
                    heading=s.heading.value,
                    ordinal=s.ordinal,
                    body=s.body,
                )
                for s in manuscript.sections
            )
        )
