from domain.manuscript.infrastructure.ports.manuscript_repository import ManuscriptRepository
from domain.manuscript.models.value_objects import ManuscriptId, SectionId


class RemoveSectionService:
    """Use case: remove a section from a manuscript."""

    def __init__(self, repository: ManuscriptRepository) -> None:
        self._repository = repository

    def execute(self, manuscript_id: str, section_id: str) -> None:
        """Remove the section; do nothing if the manuscript does not exist."""
        valid_manuscript_id = ManuscriptId.from_str(manuscript_id)
        valid_section_id = SectionId.from_str(section_id)

        manuscript = self._repository.get_by_id(valid_manuscript_id)

        if manuscript is not None:
            manuscript.remove_section(valid_section_id)

            self._repository.save(manuscript)
