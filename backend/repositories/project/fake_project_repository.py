from uuid import UUID

from domain.project.aggregates import Project
from domain.project.value_objects import ProjectName
from repositories.project.project_repository import ProjectRepository


class FakeProjectRepository(ProjectRepository):
    """In-memory project repository for development and testing.

    Attributes:
        PROJECT_ID: Matches the project id used by seeded manuscripts.
        OWNER_ID: Matches the seeded user in FakeUserRepository.
    """

    PROJECT_ID = UUID("00000000-0000-0000-0000-000000000001")
    OWNER_ID = UUID("00000000-0000-0000-0000-0000000000a1")

    def __init__(self, *, seed: bool = True) -> None:
        """Initialize the repository.

        Args:
            seed: If True, add the project the seeded manuscripts belong to.
        """
        self._projects: dict[UUID, Project] = {}

        if seed:
            self.save(
                Project(
                    id=self.PROJECT_ID,
                    owner_id=self.OWNER_ID,
                    name=ProjectName("Sample Project"),
                )
            )

    def save(self, project: Project) -> None:
        """Store a project, replacing any existing one with the same id.

        Args:
            project: The project to save.
        """
        self._projects[project.id] = project

    def get_by_id(self, project_id: UUID) -> Project | None:
        """Retrieve a project by its identifier.

        Args:
            project_id: The unique identifier of the project.

        Returns:
            The matching project, or None if not found.
        """
        return self._projects.get(project_id)

    def get_by_owner_id(self, owner_id: UUID) -> list[Project]:
        """Retrieve all projects owned by a user.

        Args:
            owner_id: The unique identifier of the owning user.

        Returns:
            A list of projects, empty if none exist.
        """
        return [p for p in self._projects.values() if p.owner_id == owner_id]

    def get_all(self) -> list[Project]:
        """Retrieve all stored projects.

        Returns:
            A list of all projects, empty if none exist.
        """
        return list(self._projects.values())

    def delete(self, project_id: UUID) -> None:
        """Delete a project by its identifier.

        Does nothing if the project does not exist.

        Args:
            project_id: The unique identifier of the project.
        """
        self._projects.pop(project_id, None)
