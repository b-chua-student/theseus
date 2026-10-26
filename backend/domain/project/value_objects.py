from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectName:
    """Immutable project name."""

    value: str

    def __post_init__(self) -> None:
        """Strip and validate the name.

        Raises:
            ValueError: If the name is empty or whitespace only.
        """
        value = self.value.strip()

        if not value:
            raise ValueError("Project name cannot be empty")

        object.__setattr__(self, "value", value)
