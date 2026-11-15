from domain.manuscript.infrastructure.ports.manuscript_repository import ManuscriptRepository
from domain.manuscript.models.value_objects import Heading, ManuscriptId, SectionId


class RenameSectionService:
    """Use case: change a section's heading."""

    def __init__(self, repository: ManuscriptRepository) -> None:
        self._repository = repository

    def execute(self, manuscript_id: str, section_id: str, new_heading: str) -> None:
        """Rename the section; do nothing if the manuscript does not exist."""
        valid_manuscript_id = ManuscriptId.from_str(manuscript_id)

        manuscript = self._repository.get_by_id(valid_manuscript_id)

        if manuscript is not None:
            valid_section_id = SectionId.from_str(section_id)
            valid_heading = Heading(new_heading)

            manuscript.rename_section(section_id=valid_section_id, new_heading=valid_heading)

            self._repository.save(manuscript)
