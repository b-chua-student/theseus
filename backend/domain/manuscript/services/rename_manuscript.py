from domain.manuscript.infrastructure.ports.manuscript_repository import ManuscriptRepository
from domain.manuscript.models.value_objects import ManuscriptId, ManuscriptTitle


class RenameManuscriptService:
    """Use case: change a manuscript's title."""

    def __init__(self, repository: ManuscriptRepository) -> None:
        self._repository = repository

    def execute(self, manuscript_id: str, new_title: str) -> None:
        """Rename the manuscript; do nothing if it does not exist."""
        valid_manuscript_id = ManuscriptId.from_str(manuscript_id)
        valid_manuscript_title = ManuscriptTitle(new_title)

        manuscript = self._repository.get_by_id(valid_manuscript_id)

        if manuscript is not None:
            manuscript.rename(valid_manuscript_title)

            self._repository.save(manuscript)
