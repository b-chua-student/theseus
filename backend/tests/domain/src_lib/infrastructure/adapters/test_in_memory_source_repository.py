"""Tests for in-memory source repository."""

from typing import Any
from uuid import uuid4

import pytest

from domain.src_lib.infrastructure.adapters.in_memory_source_repository import (
    InMemorySourceRepository,
)
from domain.src_lib.models.aggregates import Source
from domain.src_lib.models.value_objects import (
    Author,
    ContentType,
    Description,
    SourceId,
    SourceTitle,
    Tags,
    TextBody,
)


class TestInMemorySourceRepository:
    """Test the in-memory source repository."""

    @pytest.fixture
    def repo(self):
        return InMemorySourceRepository()

    @pytest.fixture
    def project_id(self):
        return uuid4()

    @pytest.fixture
    def other_project_id(self):
        return uuid4()

    def create_text_source(self, repo, project_id, **kwargs: Any):
        """Helper to create and save a text source."""
        source = Source.add_text(
            title=SourceTitle(kwargs.get("title", "Test Text")),
            content=TextBody(kwargs.get("content", "Sample content")),
            project_id=project_id,
            description=Description.create(kwargs.get("description")),
            tags=Tags.create(kwargs.get("tags", [])),
            content_type=kwargs.get("content_type", ContentType.OTHER),
        )
        repo.save(source)
        return source

    def create_file_source(self, repo, project_id, **kwargs: Any):
        """Helper to create and save a file source."""
        source = Source.add(
            title=SourceTitle(kwargs.get("title", "Test File")),
            file_ref=kwargs.get("file_ref", "/path/to/file.pdf"),
            project_id=project_id,
            authors=[Author(a) for a in kwargs.get("authors", ["John Doe"])],
            year=kwargs.get("year", 2023),
        )
        repo.save(source)
        return source

    def test_save_and_get(self, repo, project_id):
        """Should save and retrieve a source."""
        source = self.create_text_source(repo, project_id, title="Test Source")

        retrieved = repo.get(source.id)
        assert retrieved is not None
        assert retrieved.id == source.id
        assert retrieved.title.value == "Test Source"

    def test_get_nonexistent(self, repo):
        """Should return None for non-existent source."""
        source_id = SourceId.new()
        assert repo.get(source_id) is None

    def test_list_active_excludes_removed(self, repo, project_id):
        """list_active should exclude removed sources."""
        source1 = self.create_text_source(repo, project_id, title="Active 1")
        source2 = self.create_text_source(repo, project_id, title="Active 2")
        source3 = self.create_text_source(repo, project_id, title="To Remove")

        source3.remove()
        repo.save(source3)

        active_sources = repo.list_active()
        active_ids = {s.id for s in active_sources}

        assert source1.id in active_ids
        assert source2.id in active_ids
        assert source3.id not in active_ids

    def test_list_text_filters_by_project(self, repo, project_id, other_project_id):
        """list_text should only return sources from specified project."""
        # Create sources in different projects
        source1 = self.create_text_source(repo, project_id, title="Project 1 Source")
        source2 = self.create_text_source(repo, other_project_id, title="Project 2 Source")

        sources, total = repo.list_text(project_id)
        assert total == 1
        assert len(sources) == 1
        assert sources[0].id == source1.id

        sources, total = repo.list_text(other_project_id)
        assert total == 1
        assert sources[0].id == source2.id

    def test_list_text_filters_by_content_type(self, repo, project_id):
        """list_text should filter by content type."""
        source1 = self.create_text_source(
            repo, project_id, title="Documentation", content_type=ContentType.DOCUMENTATION
        )
        source2 = self.create_text_source(
            repo, project_id, title="Code", content_type=ContentType.CODE
        )
        self.create_text_source(repo, project_id, title="Other", content_type=ContentType.OTHER)

        # Filter by documentation
        sources, total = repo.list_text(project_id, content_type=ContentType.DOCUMENTATION)
        assert total == 1
        assert sources[0].id == source1.id

        # Filter by code
        sources, total = repo.list_text(project_id, content_type=ContentType.CODE)
        assert total == 1
        assert sources[0].id == source2.id

    def test_list_text_filters_by_tag(self, repo, project_id):
        """list_text should filter by tag."""
        source1 = self.create_text_source(
            repo, project_id, title="Python Source", tags=["python", "backend"]
        )
        source2 = self.create_text_source(
            repo, project_id, title="JavaScript Source", tags=["javascript", "frontend"]
        )
        source3 = self.create_text_source(
            repo, project_id, title="Multi-tag Source", tags=["python", "javascript"]
        )

        # Filter by python tag
        sources, total = repo.list_text(project_id, tag="python")
        assert total == 2
        source_ids = {s.id for s in sources}
        assert source1.id in source_ids
        assert source3.id in source_ids
        assert source2.id not in source_ids

        # Filter by javascript tag
        sources, total = repo.list_text(project_id, tag="javascript")
        assert total == 2
        source_ids = {s.id for s in sources}
        assert source2.id in source_ids
        assert source3.id in source_ids
        assert source1.id not in source_ids

    def test_list_text_excludes_file_sources(self, repo, project_id):
        """list_text should only include text sources."""
        text_source = self.create_text_source(repo, project_id, title="Text Source")
        self.create_file_source(repo, project_id, title="File Source")

        sources, total = repo.list_text(project_id)
        assert total == 1
        assert sources[0].id == text_source.id

    def test_list_text_excludes_removed_sources(self, repo, project_id):
        """list_text should exclude removed sources."""
        source1 = self.create_text_source(repo, project_id, title="Active")
        source2 = self.create_text_source(repo, project_id, title="To Remove")

        source2.remove()
        repo.save(source2)

        sources, total = repo.list_text(project_id)
        assert total == 1
        assert sources[0].id == source1.id

    def test_list_text_sorts_by_updated_at_desc(self, repo, project_id):
        """list_text should sort by updated_at descending by default."""
        import time

        source1 = self.create_text_source(repo, project_id, title="Source 1")
        time.sleep(0.01)  # Ensure different timestamps
        source2 = self.create_text_source(repo, project_id, title="Source 2")

        sources, total = repo.list_text(project_id)
        assert total == 2
        # Most recent first
        assert sources[0].id == source2.id
        assert sources[1].id == source1.id

    def test_list_text_sorts_by_title(self, repo, project_id):
        """list_text should sort by title when specified."""
        self.create_text_source(repo, project_id, title="Charlie")
        self.create_text_source(repo, project_id, title="Alpha")
        self.create_text_source(repo, project_id, title="Bravo")

        sources, total = repo.list_text(project_id, sort="title")
        assert total == 3
        assert sources[0].title.value == "Alpha"
        assert sources[1].title.value == "Bravo"
        assert sources[2].title.value == "Charlie"

    def test_list_text_pagination(self, repo, project_id):
        """list_text should support pagination."""
        # Create 5 sources
        for i in range(5):
            self.create_text_source(repo, project_id, title=f"Source {i}")

        # Page 1, size 2
        sources, total = repo.list_text(project_id, page=1, page_size=2)
        assert total == 5
        assert len(sources) == 2

        # Page 2, size 2
        sources, total = repo.list_text(project_id, page=2, page_size=2)
        assert len(sources) == 2

        # Page 3, size 2 (partial page)
        sources, total = repo.list_text(project_id, page=3, page_size=2)
        assert len(sources) == 1

        # Page 4, size 2 (empty page)
        sources, total = repo.list_text(project_id, page=4, page_size=2)
        assert len(sources) == 0

    def test_search_text_by_title(self, repo, project_id):
        """search_text should find sources by title."""
        source1 = self.create_text_source(repo, project_id, title="Python Tutorial")
        source2 = self.create_text_source(repo, project_id, title="JavaScript Guide")
        source3 = self.create_text_source(repo, project_id, title="Java Reference")

        sources, total = repo.search_text(project_id, "python")
        assert total == 1
        assert sources[0].id == source1.id

        sources, total = repo.search_text(project_id, "guide")
        assert total == 1
        assert sources[0].id == source2.id

        sources, total = repo.search_text(project_id, "java")
        assert total == 2  # Matches both JavaScript and Java
        source_ids = {s.id for s in sources}
        assert source2.id in source_ids
        assert source3.id in source_ids

    def test_search_text_by_description(self, repo, project_id):
        """search_text should find sources by description."""
        source1 = self.create_text_source(
            repo, project_id, title="Doc 1", description="This is about Python programming"
        )
        source2 = self.create_text_source(
            repo, project_id, title="Doc 2", description="JavaScript tutorial for beginners"
        )

        sources, total = repo.search_text(project_id, "python")
        assert total == 1
        assert sources[0].id == source1.id

        sources, total = repo.search_text(project_id, "tutorial")
        assert total == 1
        assert sources[0].id == source2.id

    def test_search_text_by_tags(self, repo, project_id):
        """search_text should find sources by tags."""
        source1 = self.create_text_source(
            repo, project_id, title="Source 1", tags=["python", "backend"]
        )
        source2 = self.create_text_source(
            repo, project_id, title="Source 2", tags=["javascript", "frontend"]
        )

        sources, total = repo.search_text(project_id, "python")
        assert total == 1
        assert sources[0].id == source1.id

        sources, total = repo.search_text(project_id, "frontend")
        assert total == 1
        assert sources[0].id == source2.id

    def test_search_text_by_content(self, repo, project_id):
        """search_text should find sources by content."""
        self.create_text_source(
            repo,
            project_id,
            title="Python Doc",
            content="This document explains Python functions and classes.",
        )
        source2 = self.create_text_source(
            repo,
            project_id,
            title="JS Doc",
            content="JavaScript variables and functions are explained here.",
        )

        sources, total = repo.search_text(project_id, "functions")
        assert total == 2  # Matches both

        sources, total = repo.search_text(project_id, "variables")
        assert total == 1
        assert sources[0].id == source2.id

    def test_search_text_case_insensitive(self, repo, project_id):
        """search_text should be case insensitive."""
        self.create_text_source(
            repo, project_id, title="Python Guide", content="Python is a programming language."
        )

        sources, total = repo.search_text(project_id, "python")
        assert total == 1

        sources, total = repo.search_text(project_id, "PYTHON")
        assert total == 1

        sources, total = repo.search_text(project_id, "Python")
        assert total == 1

    def test_search_text_combines_with_filters(self, repo, project_id):
        """search_text should combine with content_type and tag filters."""
        source1 = self.create_text_source(
            repo,
            project_id,
            title="Python Doc",
            content_type=ContentType.DOCUMENTATION,
            tags=["python"],
            content="Python documentation",
        )
        source2 = self.create_text_source(
            repo,
            project_id,
            title="Python Code",
            content_type=ContentType.CODE,
            tags=["python"],
            content="Python code example",
        )
        source3 = self.create_text_source(
            repo,
            project_id,
            title="JS Doc",
            content_type=ContentType.DOCUMENTATION,
            tags=["javascript"],
            content="JavaScript documentation",
        )

        # Search "python" with documentation filter
        sources, total = repo.search_text(
            project_id, "python", content_type=ContentType.DOCUMENTATION
        )
        assert total == 1
        assert sources[0].id == source1.id

        # Search "python" with code filter
        sources, total = repo.search_text(project_id, "python", content_type=ContentType.CODE)
        assert total == 1
        assert sources[0].id == source2.id

        # Search "documentation" with javascript tag filter
        sources, total = repo.search_text(project_id, "documentation", tag="javascript")
        assert total == 1
        assert sources[0].id == source3.id

    def test_search_text_empty_query_returns_all(self, repo, project_id):
        """search_text with empty query should return all matching sources."""
        self.create_text_source(repo, project_id, title="Source 1")
        self.create_text_source(repo, project_id, title="Source 2")

        sources, total = repo.search_text(project_id, "")
        assert total == 2

        sources, total = repo.search_text(project_id, "", page_size=1)
        assert total == 2
        assert len(sources) == 1

    def test_search_text_pagination(self, repo, project_id):
        """search_text should support pagination."""
        for i in range(5):
            self.create_text_source(repo, project_id, title=f"Source {i}")

        # Search for "source" should match all
        sources, total = repo.search_text(project_id, "source", page=1, page_size=2)
        assert total == 5
        assert len(sources) == 2

    def test_search_text_isolated_by_project(self, repo, project_id, other_project_id):
        """search_text should never return sources from another project."""
        mine = self.create_text_source(repo, project_id, title="Shared Term")
        self.create_text_source(repo, other_project_id, title="Shared Term")

        sources, total = repo.search_text(project_id, "shared")
        assert total == 1
        assert sources[0].id == mine.id

    def test_search_text_excludes_removed_and_file_sources(self, repo, project_id):
        """search_text should skip removed and file-kind sources."""
        active = self.create_text_source(repo, project_id, title="Needle active")
        removed = self.create_text_source(repo, project_id, title="Needle removed")
        removed.remove()
        repo.save(removed)
        self.create_file_source(repo, project_id, title="Needle file")

        sources, total = repo.search_text(project_id, "needle")
        assert total == 1
        assert sources[0].id == active.id

    def test_search_text_no_match_returns_empty(self, repo, project_id):
        """A query with no matches is valid and returns an empty page."""
        self.create_text_source(repo, project_id, title="Something")

        sources, total = repo.search_text(project_id, "zzz-nothing")
        assert sources == []
        assert total == 0

    def test_save_updates_existing_source(self, repo, project_id):
        """save should overwrite an existing source and reflect it in get/list/search."""
        source = self.create_text_source(repo, project_id, title="Old", content="old body")

        source.update_text(
            title=SourceTitle("New"),
            content=TextBody("fresh body"),
            tags=Tags.create(["updated"]),
            content_type=ContentType.NOTES,
        )
        repo.save(source)

        stored = repo.get(source.id)
        assert stored is not None
        assert stored.title.value == "New"
        assert stored.version == 2
        sources, total = repo.list_text(project_id)
        assert total == 1
        assert sources[0].content is not None
        assert sources[0].content.value == "fresh body"
        assert repo.search_text(project_id, "old")[1] == 0
        assert repo.search_text(project_id, "fresh")[1] == 1
        assert repo.list_text(project_id, tag="updated")[1] == 1

    def test_list_text_title_sort_is_case_insensitive(self, repo, project_id):
        """Title sort ignores case."""
        self.create_text_source(repo, project_id, title="bravo")
        self.create_text_source(repo, project_id, title="Alpha")

        sources, _ = repo.list_text(project_id, sort="title")
        assert [s.title.value for s in sources] == ["Alpha", "bravo"]
