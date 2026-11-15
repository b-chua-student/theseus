from domain.manuscript.infrastructure.ports.manuscript_repository import ManuscriptRepository
from domain.manuscript.models.value_objects import Heading, ManuscriptId, SectionId


class AppendSectionService:
    """Use case: append a section to a manuscript."""

    def __init__(self, repository: ManuscriptRepository) -> None:
        self.repository = repository

    def execute(self, manuscript_id: str, parent_id: str | None, heading: str) -> None:
        """Append a section, optionally under parent_id; do nothing if the manuscript is missing."""
        valid_manuscript_id = ManuscriptId.from_str(manuscript_id)

        manuscript = self.repository.get_by_id(valid_manuscript_id)

        if manuscript is not None:
            valid_parent_id = None

            if parent_id is not None:
                valid_parent_id = SectionId.from_str(parent_id)

            valid_heading = Heading(heading)
            manuscript.append_section(parent_id=valid_parent_id, heading=valid_heading)

            self.repository.save(manuscript)
