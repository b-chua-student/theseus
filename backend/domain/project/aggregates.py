from uuid import UUID

from .value_objects import ProjectName


class Project:
    """Aggregate root for a project that groups manuscripts."""

    def __init__(self, id: UUID, owner_id: UUID, name: ProjectName) -> None:
        """Create a project.

        Args:
            id: Unique identifier of the project.
            owner_id: Identifier of the owning user.
            name: Project name.
        """
        self._id = id
        self._owner_id = owner_id
        self._name = name

    @property
    def id(self) -> UUID:
        """Unique identifier of the project."""
        return self._id

    @property
    def owner_id(self) -> UUID:
        """Identifier of the owning user."""
        return self._owner_id

    @property
    def name(self) -> ProjectName:
        """Current project name."""
        return self._name

    def rename(self, new_name: ProjectName) -> None:
        """Change the project name."""
        self._name = new_name
