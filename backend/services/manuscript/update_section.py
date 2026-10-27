from uuid import UUID

from domain.manuscript.aggregates import Manuscript
from repositories.manuscript.manuscript_repository import ManuscriptRepository


class UpdateSectionService:
    """Application service for editing a section within a manuscript."""

    def __init__(self, repository: ManuscriptRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to persist manuscripts.
        """
        self._repository = repository

    def execute(
        self,
        manuscript_id: UUID,
        section_id: UUID,
        heading: str | None = None,
        body: str | None = None,
    ) -> Manuscript:
        """Edit a section's heading and/or body and persist the changes.

        Args:
            manuscript_id: Unique identifier of the manuscript.
            section_id: Unique identifier of the section to edit.
            heading: New heading text, or None to leave unchanged.
            body: New body text, or None to leave unchanged.

        Returns:
            The updated manuscript aggregate.

        Raises:
            ValueError: If the manuscript or section is not found, or if
                both heading and body are None.
        """
        manuscript = self._repository.get_by_id(manuscript_id)
        if manuscript is None:
            raise ValueError(f"Manuscript with ID {manuscript_id} not found.")

        manuscript.edit_section(section_id=section_id, heading=heading, body=body)
        self._repository.save(manuscript)

        return manuscript
