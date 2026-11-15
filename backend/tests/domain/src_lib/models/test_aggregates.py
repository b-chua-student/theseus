"""Tests for source library aggregates."""

from uuid import uuid4

import pytest

from domain.src_lib.models.aggregates import Source
from domain.src_lib.models.events import SourceAdded, SourceRemoved, SourceUpdated
from domain.src_lib.models.value_objects import (
    Author,
    ContentType,
    Description,
    SourceId,
    SourceTitle,
    Tags,
    TextBody,
)


class TestSourceAggregate:
    """Test the Source aggregate."""

    @pytest.fixture
    def project_id(self):
        return uuid4()

    @pytest.fixture
    def valid_file_source(self, project_id):
        """Create a valid file source."""
        return Source.add(
            title=SourceTitle("Test File"),
            file_ref="/path/to/file.pdf",
            project_id=project_id,
            authors=[Author("John Doe")],
            year=2023,
        )

    @pytest.fixture
    def valid_text_source(self, project_id):
        """Create a valid text source."""
        return Source.add_text(
            title=SourceTitle("Test Text"),
            content=TextBody("Sample text content"),
            project_id=project_id,
            description=Description("A test description"),
            tags=Tags.create(["tag1", "tag2"]),
            content_type=ContentType.DOCUMENTATION,
        )

    def test_create_file_source(self, project_id):
        """Creating a file source should work with required fields."""
        source = Source.add(
            title=SourceTitle("Test File"),
            file_ref="/path/to/file.pdf",
            project_id=project_id,
        )

        assert source.title.value == "Test File"
        assert source.file_ref == "/path/to/file.pdf"
        assert source.project_id == project_id
        assert source.kind == "file"
        assert source.content is None
        assert source.description is None
        assert source.tags.value == ()
        assert source.content_type == ContentType.OTHER
        assert source.version == 1
        assert source.updated_at is not None
        assert not source.is_removed

    def test_create_file_source_without_file_ref_raises_error(self, project_id):
        """Creating a file source without file_ref should raise error."""
        with pytest.raises(ValueError, match="File reference required"):
            Source.add(
                title=SourceTitle("Test"),
                file_ref="",
                project_id=project_id,
            )

    def test_create_text_source(self, project_id):
        """Creating a text source should work with required fields."""
        source = Source.add_text(
            title=SourceTitle("Test Text"),
            content=TextBody("Sample content"),
            project_id=project_id,
        )

        assert source.title.value == "Test Text"
        assert source.content.value == "Sample content"
        assert source.file_ref == ""  # Empty for text sources
        assert source.project_id == project_id
        assert source.kind == "text"
        assert source.description is None
        assert source.tags.value == ()
        assert source.content_type == ContentType.OTHER
        assert source.version == 1
        assert source.updated_at is not None
        assert not source.is_removed

    def test_create_text_source_with_all_fields(self, project_id):
        """Creating a text source with all optional fields should work."""
        source = Source.add_text(
            title=SourceTitle("Test Text"),
            content=TextBody("Sample content"),
            project_id=project_id,
            description=Description("A detailed description"),
            tags=Tags.create(["python", "testing", "documentation"]),
            content_type=ContentType.CODE,
        )

        assert source.title.value == "Test Text"
        assert source.content.value == "Sample content"
        assert source.description.value == "A detailed description"
        assert source.tags.value == ("python", "testing", "documentation")
        assert source.content_type == ContentType.CODE

    def test_create_text_source_without_content_raises_error(self, project_id):
        """Creating a text source without content should raise error."""
        with pytest.raises(ValueError, match="Content required"):
            Source.add(
                title=SourceTitle("Test"),
                file_ref="",  # Empty for text
                project_id=project_id,
                kind="text",
                content=None,
            )

    def test_file_source_invariants(self, project_id):
        """File source should not allow content."""
        Source.add(
            title=SourceTitle("Test"),
            file_ref="/path/to/file.pdf",
            project_id=project_id,
        )

        # Try to manually create an invalid file source with content
        with pytest.raises(ValueError, match="File source cannot have content"):
            Source(
                id=SourceId.new(),
                title=SourceTitle("Test"),
                authors=(),
                year=None,
                file_ref="/path/to/file.pdf",
                project_id=project_id,
                kind="file",
                content=TextBody("Invalid content"),  # Should fail
            )

    def test_text_source_invariants(self, project_id):
        """Text source should not allow file_ref."""
        # Try to manually create an invalid text source with file_ref
        with pytest.raises(ValueError, match="Text source cannot have file_ref"):
            Source(
                id=SourceId.new(),
                title=SourceTitle("Test"),
                authors=(),
                year=None,
                file_ref="/path/to/file.pdf",  # Should fail
                project_id=project_id,
                kind="text",
                content=TextBody("Valid content"),
            )

    def test_invalid_kind_raises_error(self, project_id):
        """Invalid kind should raise error in post_init."""
        with pytest.raises(ValueError, match="Invalid kind"):
            Source(
                id=SourceId.new(),
                title=SourceTitle("Test"),
                authors=(),
                year=None,
                file_ref="",
                project_id=project_id,
                kind="invalid",  # type: ignore
                content=None,
            )

    def test_update_text_source(self, valid_text_source):
        """Updating a text source should work and bump version."""
        old_version = valid_text_source.version
        old_updated_at = valid_text_source.updated_at

        # Clear existing events from creation
        valid_text_source.pull_events()

        valid_text_source.update_text(
            title=SourceTitle("Updated Title"),
            content=TextBody("Updated content"),
            description=Description("Updated description"),
            tags=Tags.create(["newtag1", "newtag2"]),
            content_type=ContentType.NOTES,
        )

        assert valid_text_source.title.value == "Updated Title"
        assert valid_text_source.content.value == "Updated content"
        assert valid_text_source.description.value == "Updated description"
        assert valid_text_source.tags.value == ("newtag1", "newtag2")
        assert valid_text_source.content_type == ContentType.NOTES
        assert valid_text_source.version == old_version + 1
        assert valid_text_source.updated_at > old_updated_at

        # Check events
        events = valid_text_source.pull_events()
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, SourceUpdated)
        assert event.source_id == valid_text_source.id
        assert event.project_id == valid_text_source.project_id
        assert event.kind == "text"
        assert event.version == valid_text_source.version

    def test_update_text_on_file_source_raises_error(self, valid_file_source):
        """Updating text on a file source should raise error."""
        with pytest.raises(ValueError, match="Can only update text on text sources"):
            valid_file_source.update_text(
                title=SourceTitle("New Title"),
                content=TextBody("Content"),
            )

    def test_update_metadata_on_text_source_bumps_version(self, valid_text_source):
        """Updating metadata on text source should bump version."""
        old_version = valid_text_source.version
        old_updated_at = valid_text_source.updated_at

        # Clear existing events from creation
        valid_text_source.pull_events()

        valid_text_source.update_metadata(
            title=SourceTitle("New Title"),
            authors=[Author("Jane Doe")],
            year=2024,
        )

        assert valid_text_source.title.value == "New Title"
        assert valid_text_source.authors[0].name == "Jane Doe"
        assert valid_text_source.year == 2024
        assert valid_text_source.version == old_version + 1
        assert valid_text_source.updated_at > old_updated_at

        # Check events
        events = valid_text_source.pull_events()
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, SourceUpdated)
        assert event.version == valid_text_source.version

    def test_update_metadata_on_file_source_does_not_bump_version(self, valid_file_source):
        """Updating metadata on file source should not bump version."""
        old_version = valid_file_source.version

        # Clear existing events from creation
        valid_file_source.pull_events()

        valid_file_source.update_metadata(
            title=SourceTitle("New Title"),
            authors=[Author("Jane Doe")],
            year=2024,
        )

        assert valid_file_source.title.value == "New Title"
        assert valid_file_source.authors[0].name == "Jane Doe"
        assert valid_file_source.year == 2024
        assert valid_file_source.version == old_version  # No version bump for file sources

        # No SourceUpdated event for file sources
        events = valid_file_source.pull_events()
        assert len(events) == 0

    def test_remove_source(self, valid_text_source):
        """Removing a source should set removed_at and create event."""
        assert not valid_text_source.is_removed

        # Clear existing events from creation
        valid_text_source.pull_events()

        valid_text_source.remove()

        assert valid_text_source.is_removed
        assert valid_text_source.removed_at is not None

        events = valid_text_source.pull_events()
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, SourceRemoved)
        assert event.source_id == valid_text_source.id
        assert event.project_id == valid_text_source.project_id

    def test_remove_idempotent(self, valid_text_source):
        """Removing an already removed source should be idempotent."""
        # Clear existing events from creation
        valid_text_source.pull_events()

        valid_text_source.remove()
        first_removed_at = valid_text_source.removed_at

        valid_text_source.remove()  # Second call
        assert valid_text_source.removed_at == first_removed_at  # Unchanged

        # Only one event should be created
        events = valid_text_source.pull_events()
        assert len(events) == 1

    def test_update_removed_source_raises_error(self, valid_text_source):
        """Updating a removed source should raise error."""
        valid_text_source.remove()

        with pytest.raises(ValueError, match="Source is removed"):
            valid_text_source.update_text(
                title=SourceTitle("New Title"),
                content=TextBody("New content"),
            )

        with pytest.raises(ValueError, match="Source is removed"):
            valid_text_source.update_metadata(
                title=SourceTitle("New Title"),
                authors=[Author("Jane Doe")],
                year=2024,
            )

    def test_source_added_event_for_file_source(self, valid_file_source):
        """File source creation should emit SourceAdded event."""
        events = valid_file_source.pull_events()
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, SourceAdded)
        assert event.source_id == valid_file_source.id
        assert event.project_id == valid_file_source.project_id
        assert event.file_ref == "/path/to/file.pdf"
        assert event.kind == "file"

    def test_source_added_event_for_text_source(self, valid_text_source):
        """Text source creation should emit SourceAdded event."""
        events = valid_text_source.pull_events()
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, SourceAdded)
        assert event.source_id == valid_text_source.id
        assert event.project_id == valid_text_source.project_id
        assert event.file_ref == ""  # Empty for text sources
        assert event.kind == "text"

    def test_events_cleared_after_pull(self, valid_text_source):
        """Events should be cleared after pulling them."""
        events1 = valid_text_source.pull_events()
        assert len(events1) == 1

        events2 = valid_text_source.pull_events()
        assert len(events2) == 0

    def test_version_tracking(self, project_id):
        """Version should increment with each text update."""
        source = Source.add_text(
            title=SourceTitle("Test"),
            content=TextBody("Content 1"),
            project_id=project_id,
        )

        assert source.version == 1

        source.update_text(
            title=SourceTitle("Updated"),
            content=TextBody("Content 2"),
        )
        assert source.version == 2

        source.update_text(
            title=SourceTitle("Updated Again"),
            content=TextBody("Content 3"),
        )
        assert source.version == 3


class TestSourceValidation:
    """Test validation of source invariants."""

    @pytest.fixture
    def project_id(self):
        return uuid4()

    def test_text_source_must_have_content_in_constructor(self, project_id):
        """Text source must have content when constructed directly."""
        with pytest.raises(ValueError, match="Text source must have content"):
            Source(
                id=SourceId.new(),
                title=SourceTitle("Test"),
                authors=(),
                year=None,
                file_ref="",
                project_id=project_id,
                kind="text",
                content=None,  # Missing content
            )

    def test_file_source_must_have_file_ref_in_constructor(self, project_id):
        """File source must have file_ref when constructed directly."""
        with pytest.raises(ValueError, match="File source must have file_ref"):
            Source(
                id=SourceId.new(),
                title=SourceTitle("Test"),
                authors=(),
                year=None,
                file_ref="",  # Missing file_ref
                project_id=project_id,
                kind="file",
                content=None,
            )

    def test_backward_compatibility_default_kind(self, project_id):
        """Existing code using default kind="file" should still work."""
        source = Source(
            id=SourceId.new(),
            title=SourceTitle("Test"),
            authors=(Author("Author"),),
            year=2023,
            file_ref="/path/to/file.pdf",
            project_id=project_id,
            # kind defaults to "file"
        )

        assert source.kind == "file"
        assert source.content is None
