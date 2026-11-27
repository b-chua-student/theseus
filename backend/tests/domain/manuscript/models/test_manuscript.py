import pytest

from domain.manuscript.models.aggregates import Manuscript
from domain.manuscript.models.errors import InvalidHeadingError, InvalidManuscriptTitleError
from domain.manuscript.models.events import ManuscriptSaved
from domain.manuscript.models.value_objects import Heading, ManuscriptTitle, ProjectId


def test_template_populates_ordered_thesis_sections() -> None:
    manuscript = Manuscript.create(ProjectId.new(), ManuscriptTitle(" Thesis "), template=True)

    assert manuscript.title.value == "Thesis"
    assert [section.heading.value for section in manuscript.sections] == [
        "Abstract",
        "Introduction",
        "Literature Review",
        "Methodology",
        "Results",
        "Discussion",
        "Conclusion",
        "References",
    ]
    assert [section.ordinal for section in manuscript.sections] == list(range(1, 9))


@pytest.mark.parametrize("title", ["  ", "a" * 257])
def test_invalid_title_is_rejected(title: str) -> None:
    with pytest.raises(InvalidManuscriptTitleError):
        ManuscriptTitle(title)


@pytest.mark.parametrize("heading", ["  ", "a" * 129])
def test_invalid_heading_is_rejected(heading: str) -> None:
    with pytest.raises(InvalidHeadingError):
        Heading(heading)


def test_editing_a_nested_section_records_a_single_save_event() -> None:
    manuscript = Manuscript.create(ProjectId.new(), ManuscriptTitle("Thesis"), template=False)
    assert manuscript.sections == []
    manuscript.append_section(None, Heading("Methods"))
    parent = manuscript.sections[0]
    manuscript.append_section(parent.id, Heading("Sampling"))
    child = manuscript.sections[1]

    manuscript.rename_section(child.id, Heading("Recruitment"))
    manuscript.edit_section_body(child.id, "Recruitment details")

    assert child.parent_id == parent.id
    assert manuscript.get_section_by_heading(Heading("Recruitment")) is child
    assert child.body == "Recruitment details"
    assert manuscript.pull_events() == [
        ManuscriptSaved(
            manuscript.id.value, manuscript.project_id.value, child.id.value, child.body
        )
    ]
    assert manuscript.pull_events() == []

    manuscript.remove_section(child.id)
    assert manuscript.sections == [parent]
