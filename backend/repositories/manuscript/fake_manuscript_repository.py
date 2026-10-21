from repositories.manuscript.manuscript_repository import ManuscriptRepository
from domain.manuscript.aggregates import Manuscript

from uuid import UUID, uuid4

from domain.manuscript.aggregates import Manuscript


class FakeManuscriptRepository(ManuscriptRepository):
    PROJECT_ID = UUID("00000000-0000-0000-0000-000000000001")

    def __init__(self, seed: bool = True) -> None:
        self._manuscripts: dict[UUID, Manuscript] = {}
        if seed:
            self._seed()

    def _seed(self) -> None:
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
        self._manuscripts[manuscript.id] = manuscript

    def get_by_id(self, manuscript_id: UUID) -> Manuscript | None:
        return self._manuscripts.get(manuscript_id)

    def get_by_project_id(self, project_id: UUID) -> list[Manuscript]:
        return [
            manuscript
            for manuscript in self._manuscripts.values()
            if manuscript.project_id == project_id
        ]

    def get_all(self) -> list[Manuscript]:
        return list(self._manuscripts.values())

    def delete(self, manuscript_id: UUID) -> None:
        self._manuscripts.pop(manuscript_id, None)

    def exists(self, manuscript_id: UUID) -> bool:
        return manuscript_id in self._manuscripts

    def clear(self) -> None:
        self._manuscripts.clear()
