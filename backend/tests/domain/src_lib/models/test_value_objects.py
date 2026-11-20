"""Unit tests for Source Library value objects."""

from uuid import uuid4

import pytest

from domain.src_lib.models.errors import (
    InvalidAuthorNameError,
    InvalidDescriptionError,
    InvalidSourceIdError,
    InvalidSourceTitleError,
    InvalidTagsError,
    InvalidTextBodyError,
)
from domain.src_lib.models.value_objects import (
    Author,
    ContentType,
    Description,
    SourceId,
    SourceTitle,
    Tags,
    TextBody,
)


def test_source_id_from_valid_uuid() -> None:
    """Verify that a valid UUID can be parsed."""
    value = uuid4()
    assert SourceId.from_str(str(value)).value == value


def test_source_id_rejects_invalid_uuid() -> None:
    """Verify that an invalid UUID is rejected."""
    with pytest.raises(InvalidSourceIdError):
        SourceId.from_str("invalid-id")


def test_source_ids_are_unique() -> None:
    """Verify that generated source identifiers differ."""
    assert SourceId.new() != SourceId.new()


def test_author_accepts_valid_name() -> None:
    """Verify that a valid author name is accepted."""
    assert Author("Juan Cruz").name == "Juan Cruz"


def test_author_rejects_blank_name() -> None:
    """Verify that blank author names are rejected."""
    with pytest.raises(InvalidAuthorNameError):
        Author("   ")


def test_title_trims_whitespace() -> None:
    """Verify that surrounding whitespace is removed."""
    assert SourceTitle("  Research Notes  ").value == "Research Notes"


def test_title_rejects_blank_value() -> None:
    """Verify that blank titles are rejected."""
    with pytest.raises(InvalidSourceTitleError):
        SourceTitle("   ")


def test_title_accepts_maximum_length() -> None:
    """Verify that a 256-character title is accepted."""
    assert SourceTitle("a" * 256).value == "a" * 256


def test_title_rejects_excessive_length() -> None:
    """Verify that titles exceeding the limit are rejected."""
    with pytest.raises(InvalidSourceTitleError):
        SourceTitle("a" * 257)


def test_description_is_optional() -> None:
    """Verify that missing and blank descriptions return None."""
    assert Description.create(None) is None
    assert Description.create("   ") is None


def test_description_accepts_maximum_length() -> None:
    """Verify that a 1000-character description is accepted."""
    assert Description("a" * 1000).value == "a" * 1000


def test_description_rejects_excessive_length() -> None:
    """Verify that oversized descriptions are rejected."""
    with pytest.raises(InvalidDescriptionError):
        Description("a" * 1001)


def test_tags_remove_duplicates_and_whitespace() -> None:
    """Verify that tags are normalized and deduplicated."""
    tags = Tags.create([" research ", "notes", "research", ""])
    assert tags.value == ("research", "notes")


def test_tags_accept_maximum_count() -> None:
    """Verify that ten unique tags are accepted."""
    tags = Tags.create([str(i) for i in range(10)])
    assert len(tags.value) == 10


def test_tags_reject_excessive_count() -> None:
    """Verify that more than ten unique tags are rejected."""
    with pytest.raises(InvalidTagsError):
        Tags.create([str(i) for i in range(11)])


def test_text_body_preserves_whitespace() -> None:
    """Verify that original text formatting is preserved."""
    content = "  Research notes\nSecond line  "
    assert TextBody(content).value == content


def test_text_body_rejects_blank_content() -> None:
    """Verify that blank text content is rejected."""
    with pytest.raises(InvalidTextBodyError):
        TextBody("   ")


def test_text_body_accepts_maximum_length() -> None:
    """Verify that text at the maximum length is accepted."""
    content = "a" * 100000
    assert TextBody(content).value == content


def test_text_body_rejects_excessive_length() -> None:
    """Verify that oversized text content is rejected."""
    with pytest.raises(InvalidTextBodyError):
        TextBody("a" * 100001)


def test_content_type_parses_valid_value() -> None:
    """Verify that a supported content type is parsed."""
    assert ContentType.from_str("notes") == ContentType.NOTES


def test_content_type_defaults_to_other() -> None:
    """Verify the fallback for missing or unknown types."""
    assert ContentType.from_str(None) == ContentType.OTHER
    assert ContentType.from_str("unknown") == ContentType.OTHER
