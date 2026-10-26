from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Email:
    """Immutable, normalized email address.

    Attributes:
        value: The address, stripped and lowercased.
    """

    value: str

    def __post_init__(self) -> None:
        """Strip, lowercase, and validate the address.

        Raises:
            ValueError: If the address is empty or lacks a valid shape.
        """
        value = self.value.strip().lower()
        local, _, domain = value.partition("@")

        if not local or "." not in domain:
            raise ValueError("Invalid email address")

        object.__setattr__(self, "value", value)


@dataclass(frozen=True, slots=True)
class DisplayName:
    """Immutable user display name.

    Attributes:
        value: The name, stripped of surrounding whitespace.
    """

    value: str

    def __post_init__(self) -> None:
        """Strip and validate the name.

        Raises:
            ValueError: If the name is empty or whitespace only.
        """
        value = self.value.strip()

        if not value:
            raise ValueError("Display name cannot be empty")

        object.__setattr__(self, "value", value)
