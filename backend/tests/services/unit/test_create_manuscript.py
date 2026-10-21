from uuid import uuid4

import pytest

from domain.manuscript.aggregates import Manuscript


def test_create_manuscript():
    manuscript_id = uuid4()
    project_id = uuid4()

    manuscript = Manuscript(
        id=manuscript_id,
        project_id=project_id,
        title="Research Paper",
    )

    assert manuscript.id == manuscript_id
    assert manuscript.project_id == project_id
    assert manuscript.title == "Research Paper"
    assert manuscript.sections == ()


def test_create_manuscript_with_empty_title_fails():
    with pytest.raises(ValueError, match="title"):
        Manuscript(
            id=uuid4(),
            project_id=uuid4(),
            title="",
        )


def test_create_manuscript_with_whitespace_title_fails():
    with pytest.raises(ValueError, match="title"):
        Manuscript(
            id=uuid4(),
            project_id=uuid4(),
            title="   ",
        )


def test_create_manuscript_trims_title():
    manuscript = Manuscript(
        id=uuid4(),
        project_id=uuid4(),
        title="  Research Paper  ",
    )

    assert manuscript.title == "Research Paper"


def test_create_manuscript_has_no_sections():
    manuscript = Manuscript(
        id=uuid4(),
        project_id=uuid4(),
        title="Research Paper",
    )

    assert manuscript.sections == ()
