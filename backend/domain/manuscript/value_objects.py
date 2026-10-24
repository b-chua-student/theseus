from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Heading:
    """Immutable value object representing a section heading.

    Attributes:
        value: The heading text, stripped of surrounding whitespace.
    """

    value: str

    def __post_init__(self) -> None:
        """Validate and normalize the heading after initialization.

        Raises:
            ValueError: If the heading is empty or whitespace only.
        """
        value = self.value.strip()

        if not value:
            raise ValueError("Heading cannot be empty")

        object.__setattr__(self, "value", value)


@dataclass(frozen=True, slots=True)
class Body:
    """Immutable value object representing a section body.

    Attributes:
        value: The body text. Defaults to an empty string.
    """

    value: str = ""
