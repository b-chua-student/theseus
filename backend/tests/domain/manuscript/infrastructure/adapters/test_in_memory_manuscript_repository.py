from domain.manuscript.infrastructure.adapters.in_memory_manuscript_repository import (
    InMemoryManuscriptRepository,
)
from domain.manuscript.models.aggregates import Manuscript
from domain.manuscript.models.value_objects import Heading, ManuscriptTitle, ProjectId


def test_repository_filters_projects_and_persists_edits_and_deletion() -> None:
    repository = InMemoryManuscriptRepository(template=False)
    manuscript = Manuscript.create(ProjectId.new(), ManuscriptTitle("Thesis"), template=False)
    other = Manuscript.create(ProjectId.new(), ManuscriptTitle("Notes"), template=False)
    repository.save(manuscript)
    repository.save(other)

    assert [item.id for item in repository.list_by_project_id(manuscript.project_id)] == [
        manuscript.id
    ]

    manuscript.append_section(None, Heading("Introduction"))
    repository.save(manuscript)
    stored = repository.get_by_id(manuscript.id)
    assert stored is not None
    assert [section.heading.value for section in stored.sections] == ["Introduction"]

    repository.delete(manuscript.id)
    assert repository.get_by_id(manuscript.id) is None
    assert repository.get_by_id(other.id) is not None
