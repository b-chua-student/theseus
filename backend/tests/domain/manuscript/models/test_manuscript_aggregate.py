import pytest

from domain.manuscript.models.aggregates import DEFAULT_THESIS_TEMPLATE, Manuscript
from domain.manuscript.models.errors import InvalidManuscriptTitleError, InvalidProjectIdError
from domain.manuscript.models.value_objects import Heading, ManuscriptTitle, ProjectId


def test_invalid_project_id_raises_error() -> None:
    with pytest.raises(InvalidProjectIdError):
        ProjectId.from_str("abc")


def test_invalid_manuscript_title_raises_error() -> None:
    with pytest.raises(InvalidManuscriptTitleError):
        ManuscriptTitle("a" * 300)


def test_create_manuscript_with_template() -> None:
    manuscript = Manuscript.create(
        project_id=ProjectId.new(),
        title=ManuscriptTitle("Test Manuscript"),
        template=True,
    )

    assert [section.heading.value for section in manuscript.sections] == list(
        DEFAULT_THESIS_TEMPLATE
    )


def test_append_section() -> None:
    heading = "Test Heading"

    manuscript = Manuscript.create(
        project_id=ProjectId.new(),
        title=ManuscriptTitle("Test Manuscript"),
        template=False,
    )

    manuscript.append_section(None, Heading(heading))

    assert any(section.heading.value == heading for section in manuscript.sections)


def test_rename_section() -> None:
    heading = "Test Heading"

    manuscript = Manuscript.create(
        project_id=ProjectId.new(),
        title=ManuscriptTitle("Test Manuscript"),
        template=False,
    )

    manuscript.append_section(None, Heading(heading))

    assert any(section.heading.value == heading for section in manuscript.sections)

    new_heading = "New Heading"
    section = manuscript.get_section_by_heading(Heading(heading))
    if section is not None:
        manuscript.rename_section(section.id, Heading(new_heading))

    assert any(section.heading.value == new_heading for section in manuscript.sections)


def test_edit_section_body() -> None:
    heading = "Test Heading"

    manuscript = Manuscript.create(
        project_id=ProjectId.new(),
        title=ManuscriptTitle("Test Manuscript"),
        template=False,
    )

    manuscript.append_section(None, Heading(heading))
    section = manuscript.get_section_by_heading(Heading(heading))
    new_body = "New Body"
    if section is not None:
        manuscript.edit_section_body(section.id, new_body)

    assert any(section.body == new_body for section in manuscript.sections)
