"""Tests for the assistant's indexed library sources read endpoint (T-006, D-009)."""

from uuid import uuid4

from domain.assistant.models.aggregates import IndexedDocument
from domain.assistant.models.value_objects import (
    Chunk,
    ChunkId,
    DocumentRefId,
    IndexedDocumentTitle,
)
from domain.assistant.models.value_objects import ProjectId as AssistantProjectId
from tests.domain.assistant.features.combined_context_support import CombinedContextHarness


def _indexed(harness: CombinedContextHarness, ref: DocumentRefId, title: str) -> None:
    document = IndexedDocument.create(
        IndexedDocumentTitle(title), ref, AssistantProjectId(harness.project_id)
    )
    document.start_indexing()
    document.complete_indexing(
        [Chunk(id=ChunkId.new(), text=title, position="1", location="p1", content_hash=title)]
    )
    harness.documents.add(document)


def _source_ids(harness: CombinedContextHarness) -> list[str]:
    response = harness.client.get(f"/api/projects/{harness.project_id}/indexed-sources")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    return sorted(data["source_ids"])


def test_lists_the_searchable_library_sources_of_the_project() -> None:
    harness = CombinedContextHarness()
    methods = harness.add_source("Methods")
    replication = harness.add_source("Replication")

    assert _source_ids(harness) == sorted([str(methods.value), str(replication.value)])


def test_excludes_manuscript_documents_indexed_in_the_same_repository() -> None:
    harness = CombinedContextHarness()
    methods = harness.add_source("Methods")
    _indexed(harness, DocumentRefId.new(), "Manuscript")

    assert _source_ids(harness) == [str(methods.value)]


def test_excludes_sources_that_are_not_searchable_yet() -> None:
    harness = CombinedContextHarness()
    methods = harness.add_source("Methods")
    pending = harness.add_source("Pending")
    document = harness.documents.get_by_doc_ref_id(pending)
    assert document is not None
    document.mark_stale()
    harness.documents.save(document)

    assert _source_ids(harness) == [str(methods.value)]


def test_excludes_sources_of_another_project() -> None:
    harness = CombinedContextHarness()
    methods = harness.add_source("Methods")
    harness.add_source("Foreign", project_id=uuid4())

    assert _source_ids(harness) == [str(methods.value)]


def test_requires_a_signed_in_member_of_the_project() -> None:
    harness = CombinedContextHarness()
    with harness.client.session_transaction() as session:
        session.clear()

    response = harness.client.get(f"/api/projects/{harness.project_id}/indexed-sources")

    assert response.status_code == 401
