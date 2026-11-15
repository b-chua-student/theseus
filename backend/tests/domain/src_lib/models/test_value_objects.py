"""Tests for source library value objects."""

import pytest

from domain.src_lib.models.errors import (
    InvalidDescriptionError,
    InvalidTagsError,
    InvalidTextBodyError,
)
from domain.src_lib.models.value_objects import (
    ContentType,
    Description,
    Tags,
    TextBody,
)


class TestDescription:
    """Test the Description value object."""

    def test_create_with_valid_description(self):
        """Creating a Description with a valid string should succeed."""
        desc = Description("A valid description")
        assert desc.value == "A valid description"

    def test_create_with_long_description_raises_error(self):
        """Creating a Description exceeding the maximum length should raise an error."""
        long_desc = "x" * 1001
        with pytest.raises(InvalidDescriptionError) as excinfo:
            Description(long_desc)
        assert "too long" in str(excinfo.value)
        assert "Maximum is 1000" in str(excinfo.value)

    def test_create_with_empty_string_returns_empty(self):
        """Creating a Description with an empty string should store empty string."""
        desc = Description("")
        assert desc.value == ""

    def test_strips_whitespace(self):
        """Description should strip surrounding whitespace."""
        desc = Description("  Some description  ")
        assert desc.value == "Some description"

    def test_create_classmethod_returns_none_for_empty(self):
        """The create classmethod should return None for None or empty strings."""
        assert Description.create(None) is None
        assert Description.create("") is None
        assert Description.create("   ") is None

    def test_create_classmethod_creates_instance_for_non_empty(self):
        """The create classmethod should create an instance for non-empty strings."""
        desc = Description.create("Valid description")
        assert isinstance(desc, Description)
        assert desc.value == "Valid description"


class TestTags:
    """Test the Tags value object."""

    def test_create_with_valid_tags(self):
        """Creating Tags with a valid list should succeed."""
        tags = Tags.create(["tag1", "tag2", "tag3"])
        assert tags.value == ("tag1", "tag2", "tag3")

    def test_create_with_too_many_tags_raises_error(self):
        """Creating Tags with more than 10 tags should raise an error."""
        many_tags = [f"tag{i}" for i in range(11)]
        with pytest.raises(InvalidTagsError) as excinfo:
            Tags.create(many_tags)
        assert "Too many tags" in str(excinfo.value)
        assert "Maximum is 10" in str(excinfo.value)

    def test_strips_and_deduplicates_tags(self):
        """Tags should strip whitespace and deduplicate."""
        tags = Tags.create(["  tag1  ", "tag2", "tag1", "  tag3  "])
        assert tags.value == ("tag1", "tag2", "tag3")

    def test_removes_empty_tags(self):
        """Empty tags should be filtered out."""
        tags = Tags.create(["tag1", "", "tag2", "   "])
        assert tags.value == ("tag1", "tag2")

    def test_create_with_none_or_empty_list(self):
        """Creating Tags with None or empty list should return empty tuple."""
        tags1 = Tags.create(None)
        assert tags1.value == ()

        tags2 = Tags.create([])
        assert tags2.value == ()

    def test_preserves_order(self):
        """Tags should preserve order after deduplication."""
        tags = Tags.create(["c", "a", "b", "c", "a"])
        assert tags.value == ("c", "a", "b")


class TestContentType:
    """Test the ContentType enum."""

    def test_valid_values(self):
        """All expected content type values should be valid."""
        assert ContentType.DOCUMENTATION.value == "documentation"
        assert ContentType.NOTES.value == "notes"
        assert ContentType.CODE.value == "code"
        assert ContentType.OTHER.value == "other"

    def test_from_str_with_valid_strings(self):
        """from_str should parse valid strings correctly."""
        assert ContentType.from_str("documentation") == ContentType.DOCUMENTATION
        assert ContentType.from_str("notes") == ContentType.NOTES
        assert ContentType.from_str("code") == ContentType.CODE
        assert ContentType.from_str("other") == ContentType.OTHER

    def test_from_str_with_none_returns_other(self):
        """from_str with None should default to OTHER."""
        assert ContentType.from_str(None) == ContentType.OTHER

    def test_from_str_with_invalid_string_returns_other(self):
        """from_str with invalid string should default to OTHER."""
        assert ContentType.from_str("invalid") == ContentType.OTHER
        assert ContentType.from_str("") == ContentType.OTHER


class TestTextBody:
    """Test the TextBody value object."""

    def test_create_with_valid_text(self):
        """Creating TextBody with valid text should succeed."""
        text = "This is some valid text content."
        body = TextBody(text)
        assert body.value == text

    def test_create_with_empty_text_raises_error(self):
        """Creating TextBody with empty text should raise an error."""
        with pytest.raises(InvalidTextBodyError) as excinfo:
            TextBody("")
        assert "cannot be empty" in str(excinfo.value)

        with pytest.raises(InvalidTextBodyError) as excinfo:
            TextBody("   ")
        assert "cannot be empty" in str(excinfo.value)

    def test_create_with_too_long_text_raises_error(self):
        """Creating TextBody exceeding 100,000 characters should raise an error."""
        long_text = "x" * 100001
        with pytest.raises(InvalidTextBodyError) as excinfo:
            TextBody(long_text)
        assert "too long" in str(excinfo.value)
        assert "Maximum is 100,000" in str(excinfo.value)

    def test_accepts_100k_characters(self):
        """TextBody should accept exactly 100,000 characters."""
        exact_text = "x" * 100000
        body = TextBody(exact_text)
        assert len(body.value) == 100000

    def test_preserves_whitespace_and_encoding(self):
        """TextBody should preserve whitespace and UTF-8 characters."""
        text = "  Line 1\n  Line 2\n  UTF-8: café, naïve, 🚀  "
        body = TextBody(text)
        assert body.value == text

    def test_boundary_tests(self):
        """Test boundary cases: 0/1/100000/100001 characters."""
        # 0 chars - should fail
        with pytest.raises(InvalidTextBodyError):
            TextBody("")

        # 1 char - should succeed
        body = TextBody("x")
        assert body.value == "x"

        # 100,000 chars - should succeed
        max_text = "x" * 100000
        body = TextBody(max_text)
        assert len(body.value) == 100000

        # 100,001 chars - should fail
        too_long = "x" * 100001
        with pytest.raises(InvalidTextBodyError):
            TextBody(too_long)


class TestIntegration:
    """Integration tests for value objects."""

    def test_description_boundaries(self):
        """Test description boundaries per requirements."""
        # 1000 chars - should succeed
        valid_desc = "x" * 1000
        desc = Description(valid_desc)
        assert len(desc.value) == 1000

        # 1001 chars - should fail
        invalid_desc = "x" * 1001
        with pytest.raises(InvalidDescriptionError):
            Description(invalid_desc)

    def test_tags_boundaries(self):
        """Test tags boundaries per requirements."""
        # 10 tags - should succeed
        ten_tags = [f"tag{i}" for i in range(10)]
        tags = Tags.create(ten_tags)
        assert len(tags.value) == 10

        # 11 tags - should fail
        eleven_tags = [f"tag{i}" for i in range(11)]
        with pytest.raises(InvalidTagsError):
            Tags.create(eleven_tags)

        # 0 tags - should succeed (empty tuple)
        tags = Tags.create([])
        assert tags.value == ()
