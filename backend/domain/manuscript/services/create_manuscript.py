from domain.manuscript.infrastructure.ports.manuscript_repository import ManuscriptRepository
from domain.manuscript.models.aggregates import Manuscript
from domain.manuscript.models.value_objects import ManuscriptTitle, ProjectId


class CreateManuscriptService:
    """Use case: create and persist a new manuscript."""

    def __init__(self, repository: ManuscriptRepository) -> None:
        self._repository = repository

    def execute(self, project_id: str, title: str, *, template: bool) -> Manuscript:
        """Create a manuscript in the project, prepopulated with sections if template is set."""
        valid_project_id = ProjectId.from_str(project_id)
        valid_manuscript_title = ManuscriptTitle(title)

        manuscript = Manuscript.create(
            project_id=valid_project_id,
            title=valid_manuscript_title,
            template=template,
        )

        self._repository.save(manuscript)

        return manuscript
