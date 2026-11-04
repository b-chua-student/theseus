from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ManuscriptSaved:
    """Emitted when the body of a manuscript section is edited and persisted.

    The assistant context subscribes to this event to keep its context window
    for the manuscript up to date (re-index or refresh the working context).

    Attributes:
        manuscript_id: UUID of the manuscript that was edited.
        project_id:    UUID of the project the manuscript belongs to.
        section_id:    UUID of the specific section whose body changed.
        body:          The full updated body text of the section.
    """

    manuscript_id: UUID
    project_id: UUID
    section_id: UUID
    body: str
