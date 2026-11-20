"""Unit tests for Source Library aggregates."""

from uuid import uuid4

import pytest

from domain.src_lib.models.aggregates import Source
from domain.src_lib.models.events import (
    SourceAdded,
    SourceRemoved,
    SourceUpdated,
)
from domain.src_lib.models.value_objects import (
    Author,
    SourceTitle,
    Tags,
    TextBody,
)


@pytest.fixture
def text_source() -> Source:
    """Create a text source for testing."""
    return Source.add_text(
        title=SourceTitle("Research Notes"),
        content=TextBody("Sample research content"),
        project_id=uuid4(),
    )


@pytest.fixture
def file_source() -> Source:
    """Create a file source for testing."""
    return Source.add(
        title=SourceTitle("Research Paper"),
        file_ref="research.pdf",
        project_id=uuid4(),
    )


def test_create_text_source(text_source: Source) -> None:
    """Verify initial text source properties."""
    assert text_source.kind == "text"
    assert text_source.file_ref is None
    assert text_source.content == TextBody("Sample research content")
    assert text_source.version == 1
    assert not text_source.is_removed


def test_create_file_source(file_source: Source) -> None:
    """Verify initial file source properties."""
    assert file_source.kind == "file"
    assert file_source.file_ref == "research.pdf"
    assert file_source.content is None


def test_file_source_requires_reference() -> None:
    """Reject file sources without a file reference."""
    with pytest.raises(ValueError, match="File reference required"):
        Source.add(
            title=SourceTitle("Research Paper"),
            file_ref=None,
            project_id=uuid4(),
        )


def test_text_source_requires_content() -> None:
    """Reject text sources without content."""
    with pytest.raises(ValueError, match="Content required"):
        Source.add(
            title=SourceTitle("Notes"),
            file_ref=None,
            project_id=uuid4(),
            kind="text",
        )


def test_text_source_rejects_file_reference() -> None:
    """Reject text sources containing a file reference."""
    with pytest.raises(ValueError, match="cannot have file_ref"):
        Source.add(
            title=SourceTitle("Notes"),
            file_ref="notes.pdf",
            project_id=uuid4(),
            kind="text",
            content=TextBody("Sample content"),
        )


def test_file_source_rejects_text_content() -> None:
    """Reject file sources containing text content."""
    with pytest.raises(ValueError, match="cannot have content"):
        Source.add(
            title=SourceTitle("Paper"),
            file_ref="paper.pdf",
            project_id=uuid4(),
            content=TextBody("Sample content"),
        )


def test_source_added_event(text_source: Source) -> None:
    """Verify creation records a SourceAdded event."""
    events = text_source.pull_events()

    assert len(events) == 1
    assert isinstance(events[0], SourceAdded)


def test_update_text_source(text_source: Source) -> None:
    """Verify text updates replace content and increment version."""
    text_source.update_text(
        title=SourceTitle("Updated Notes"),
        content=TextBody("Updated content"),
    )

    assert text_source.title == SourceTitle("Updated Notes")
    assert text_source.content == TextBody("Updated content")
    assert text_source.version == 2


def test_update_text_records_event(text_source: Source) -> None:
    """Verify text updates record a SourceUpdated event."""
    text_source.pull_events()

    text_source.update_text(
        title=SourceTitle("Updated Notes"),
        content=TextBody("Updated content"),
    )

    events = text_source.pull_events()

    assert len(events) == 1
    assert isinstance(events[0], SourceUpdated)


def test_update_text_rejects_file_source(file_source: Source) -> None:
    """Prevent text updates on file sources."""
    with pytest.raises(ValueError, match="Can only update text"):
        file_source.update_text(
            title=SourceTitle("Updated Paper"),
            content=TextBody("Updated content"),
        )


def test_update_metadata(text_source: Source) -> None:
    """Verify metadata replacement and version increment."""
    author = Author("Juan Cruz")

    text_source.update_metadata(
        title=SourceTitle("New Title"),
        authors=[author],
        year=2026,
    )

    assert text_source.title == SourceTitle("New Title")
    assert text_source.authors == (author,)
    assert text_source.year == 2026
    assert text_source.version == 2


def test_file_metadata_preserves_version(file_source: Source) -> None:
    """Verify file metadata updates preserve the version."""
    file_source.update_metadata(
        title=SourceTitle("New Paper"),
        authors=[],
        year=2026,
    )

    assert file_source.version == 1


def test_remove_source(text_source: Source) -> None:
    """Verify removal marks the source as deleted."""
    text_source.remove()

    assert text_source.is_removed
    assert text_source.removed_at is not None


def test_remove_records_event(text_source: Source) -> None:
    """Verify removal records a SourceRemoved event."""
    text_source.pull_events()
    text_source.remove()

    events = text_source.pull_events()

    assert len(events) == 1
    assert isinstance(events[0], SourceRemoved)


def test_remove_is_idempotent(text_source: Source) -> None:
    """Verify repeated removal does not create additional events."""
    text_source.pull_events()
    text_source.remove()
    removed_at = text_source.removed_at
    text_source.remove()

    assert text_source.removed_at == removed_at
    assert len(text_source.pull_events()) == 1


def test_removed_source_rejects_text_update(text_source: Source) -> None:
    """Prevent text updates after removal."""
    text_source.remove()

    with pytest.raises(ValueError, match="Source is removed"):
        text_source.update_text(
            title=SourceTitle("Updated Notes"),
            content=TextBody("Updated content"),
        )


def test_removed_source_rejects_metadata_update(text_source: Source) -> None:
    """Prevent metadata updates after removal."""
    text_source.remove()

    with pytest.raises(ValueError, match="Source is removed"):
        text_source.update_metadata(
            title=SourceTitle("New Title"),
            authors=[],
            year=None,
        )


def test_pull_events_clears_events(text_source: Source) -> None:
    """Verify pending events are cleared after retrieval."""
    assert len(text_source.pull_events()) == 1
    assert text_source.pull_events() == []


def test_default_tags_are_empty(text_source: Source) -> None:
    """Verify sources have empty tags by default."""
    assert text_source.tags == Tags(())


def test_source_creation_timestamps(text_source: Source) -> None:
    """Verify creation and update timestamps are initialized."""
    assert text_source.created_at is not None
    assert text_source.updated_at is not None
    assert text_source.created_at == text_source.updated_at
