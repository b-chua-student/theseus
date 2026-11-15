from uuid import UUID, uuid4

from domain.manuscript.aggregates import Manuscript
from repositories.manuscript.manuscript_repository import ManuscriptRepository


class FakeManuscriptRepository(ManuscriptRepository):
    """In-memory manuscript repository for development and testing.

    Attributes:
        PROJECT_ID: Project identifier assigned to seeded manuscripts.
    """

    PROJECT_ID = UUID("00000000-0000-0000-0000-000000000001")

    def __init__(self, *, seed: bool = True) -> None:
        """Initialize the repository.

        Args:
            seed: If True, populate the repository with sample manuscripts.
        """
        self._manuscripts: dict[UUID, Manuscript] = {}
        if seed:
            self._seed()

    def _seed(self) -> None:
        """Populate the repository with sample manuscripts and sections."""
        titles = [
            "The Long Winter",
            "Notes on Cartography",
            "A Field Guide to Birds",
        ]

        for title in titles:
            manuscript = Manuscript(
                id=uuid4(),
                project_id=self.PROJECT_ID,
                title=title,
            )

            part = manuscript.add_section("Part One", "Opening part.")
            manuscript.add_section("Chapter 1", "First chapter.", parent_id=part.id)
            manuscript.add_section("Chapter 2", "Second chapter.", parent_id=part.id)
            manuscript.add_section("Part Two", "Closing part.")

            self._manuscripts[manuscript.id] = manuscript

    def save(self, manuscript: Manuscript) -> None:
        """Store a manuscript, replacing any existing one with the same id.

        Args:
            manuscript: The manuscript to save.
        """
        self._manuscripts[manuscript.id] = manuscript

    def get_by_id(self, manuscript_id: UUID) -> Manuscript | None:
        """Retrieve a manuscript by its identifier.

        Args:
            manuscript_id: The unique identifier of the manuscript.

        Returns:
            The matching manuscript, or None if not found.
        """
        return self._manuscripts.get(manuscript_id)

    def get_by_project_id(self, project_id: UUID) -> list[Manuscript]:
        """Retrieve all manuscripts belonging to a project.

        Args:
            project_id: The unique identifier of the project.

        Returns:
            A list of manuscripts for the project, empty if none exist.
        """
        return [
            manuscript
            for manuscript in self._manuscripts.values()
            if manuscript.project_id == project_id
        ]

    def get_all(self) -> list[Manuscript]:
        """Retrieve all stored manuscripts.

        Returns:
            A list of all manuscripts, empty if none exist.
        """
        return list(self._manuscripts.values())

    def delete(self, manuscript_id: UUID) -> None:
        """Delete a manuscript by its identifier.

        Does nothing if the manuscript does not exist.

        Args:
            manuscript_id: The unique identifier of the manuscript.
        """
        self._manuscripts.pop(manuscript_id, None)

    def exists(self, manuscript_id: UUID) -> bool:
        """Check whether a manuscript exists.

        Args:
            manuscript_id: The unique identifier of the manuscript.

        Returns:
            True if the manuscript exists, otherwise False.
        """
        return manuscript_id in self._manuscripts

    def clear(self) -> None:
        """Remove all manuscripts from the repository."""
        self._manuscripts.clear()
