from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Heading:
    value: str

    def __post_init__(self) -> None:
        value = self.value.strip()

        if not value:
            raise ValueError("Heading cannot be empty")

        object.__setattr__(self, "value", value)


@dataclass(frozen=True, slots=True)
class Body:
    value: str = ""
