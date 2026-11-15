"""Assistant handlers for source add/update/remove, including text sources (R11)."""

from __future__ import annotations

from uuid import uuid4

import pytest

from domain.assistant.infrastructure.adapters.in_memory_indexed_document_repository import (
    InMemoryIndexedDocumentRepository,
)
from domain.assistant.infrastructure.adapters.source_library_content_provider import (
    SourceLibraryContentProvider,
)
from domain.assistant.infrastructure.ports.index_job_queue import IndexJobQueue
from domain.assistant.infrastructure.ports.source_content_provider import SourceContentProvider
from domain.assistant.models.value_objects import DocumentRefId, IndexStatus
from domain.assistant.services.handlers.on_source_added import OnSourceAdded
from domain.assistant.services.handlers.on_source_removed import OnSourceRemoved
from domain.assistant.services.handlers.on_source_updated import OnSourceUpdated
from domain.src_lib.infrastructure.adapters.in_memory_source_repository import (
    InMemorySourceRepository,
)
from domain.src_lib.models.aggregates import Source
from domain.src_lib.models.value_objects import SourceTitle, TextBody


class RecordingQueue(IndexJobQueue):
    def __init__(self) -> None:
        self.enqueued: list[DocumentRefId] = []

    def enqueue_index(self, doc_ref_id: DocumentRefId) -> None:
        self.enqueued.append(doc_ref_id)

    def set_worker(self, worker) -> None:  # noqa: ANN001
        pass


class ManuscriptStub(SourceContentProvider):
    def get_content(self, doc_ref_id: DocumentRefId) -> str:
        return "manuscript body"


@pytest.fixture
def env():
    sources = InMemorySourceRepository()
    docs = InMemoryIndexedDocumentRepository()
    queue = RecordingQueue()
    provider = SourceLibraryContentProvider(sources, ManuscriptStub())
    return sources, docs, queue, provider


def _text_source(project_id=None, title="Notes", body="hello text") -> Source:
    return Source.add_text(SourceTitle(title), TextBody(body), project_id or uuid4())


def _file_source(project_id=None) -> Source:
    return Source.add(SourceTitle("Paper"), "files/paper.pdf", project_id or uuid4())


def test_added_text_source_creates_pending_doc_with_source_title(env):
    sources, docs, queue, provider = env
    src = _text_source()
    sources.save(src)
    event = src.pull_events()[0]

    OnSourceAdded(docs, queue, provider)(event)

    ref = DocumentRefId(src.id.value)
    doc = docs.get_by_doc_ref_id(ref)
    assert doc is not None
    assert doc.title.value == "Notes"
    assert doc.status is IndexStatus.PENDING
    assert queue.enqueued == [ref]


def test_added_text_source_without_provider_uses_fallback_title(env):
    _, docs, queue, _ = env
    src = _text_source()
    event = src.pull_events()[0]

    OnSourceAdded(docs, queue, None)(event)  # type: ignore[arg-type]

    doc = docs.get_by_doc_ref_id(DocumentRefId(src.id.value))
    assert doc is not None
    assert str(src.id.value) in doc.title.value


def test_added_file_source_path_unchanged(env):
    sources, docs, queue, provider = env
    src = _file_source()
    sources.save(src)
    event = src.pull_events()[0]

    OnSourceAdded(docs, queue, provider)(event)

    ref = DocumentRefId(src.id.value)
    doc = docs.get_by_doc_ref_id(ref)
    assert doc is not None
    assert doc.title.value == "files/paper.pdf"
    assert queue.enqueued == [ref]


def test_updated_marks_indexed_doc_stale_renames_and_enqueues(env):
    sources, docs, queue, provider = env
    src = _text_source()
    sources.save(src)
    OnSourceAdded(docs, queue, provider)(src.pull_events()[0])
    ref = DocumentRefId(src.id.value)
    doc = docs.get_by_doc_ref_id(ref)
    doc.start_indexing()
    from domain.assistant.models.value_objects import Chunk, ChunkId

    doc.complete_indexing(
        [Chunk(id=ChunkId.new(), text="old", position="0", location="l", content_hash="h")]
    )
    docs.save(doc)
    queue.enqueued.clear()

    src.update_text(SourceTitle("Renamed"), TextBody("new content"))
    sources.save(src)
    OnSourceUpdated(docs, queue, provider)(src.pull_events()[0])

    doc = docs.get_by_doc_ref_id(ref)
    assert doc.status is IndexStatus.PENDING
    assert not doc.is_searchable
    assert doc.title.value == "Renamed"
    assert queue.enqueued == [ref]


def test_updated_unknown_doc_creates_it(env):
    sources, docs, queue, provider = env
    src = _text_source()
    sources.save(src)
    src.pull_events()
    src.update_text(SourceTitle("T2"), TextBody("x"))

    OnSourceUpdated(docs, queue, provider)(src.pull_events()[0])

    doc = docs.get_by_doc_ref_id(DocumentRefId(src.id.value))
    assert doc is not None and doc.title.value == "T2"
    assert queue.enqueued == [DocumentRefId(src.id.value)]


def test_updated_while_indexing_keeps_status_and_enqueues(env):
    sources, docs, queue, provider = env
    src = _text_source()
    sources.save(src)
    OnSourceAdded(docs, queue, provider)(src.pull_events()[0])
    ref = DocumentRefId(src.id.value)
    doc = docs.get_by_doc_ref_id(ref)
    doc.start_indexing()
    docs.save(doc)
    queue.enqueued.clear()

    src.update_text(SourceTitle("T"), TextBody("y"))
    OnSourceUpdated(docs, queue, provider)(src.pull_events()[0])

    assert docs.get_by_doc_ref_id(ref).status is IndexStatus.INDEXING
    assert queue.enqueued == [ref]


def test_removed_text_source_is_no_longer_searchable(env):
    sources, docs, queue, provider = env
    src = _text_source()
    sources.save(src)
    OnSourceAdded(docs, queue, provider)(src.pull_events()[0])
    ref = DocumentRefId(src.id.value)
    doc = docs.get_by_doc_ref_id(ref)
    doc.start_indexing()
    from domain.assistant.models.value_objects import Chunk, ChunkId

    doc.complete_indexing(
        [Chunk(id=ChunkId.new(), text="c", position="0", location="l", content_hash="h")]
    )
    docs.save(doc)

    src.remove()
    OnSourceRemoved(docs)(src.pull_events()[0])

    assert not docs.get_by_doc_ref_id(ref).is_searchable


def test_provider_returns_text_content_and_title(env):
    sources, _, _, provider = env
    src = _text_source(body="the body")
    sources.save(src)
    ref = DocumentRefId(src.id.value)

    assert provider.get_content(ref) == "the body"
    assert provider.get_title(ref) == "Notes"


def test_provider_delegates_non_text_ids_to_fallback(env):
    sources, _, _, provider = env
    file_src = _file_source()
    sources.save(file_src)

    assert provider.get_content(DocumentRefId(file_src.id.value)) == "manuscript body"
    assert provider.get_content(DocumentRefId(uuid4())) == "manuscript body"
    assert provider.get_title(DocumentRefId(uuid4())) is None


def test_provider_rejects_removed_text_source(env):
    sources, _, _, provider = env
    src = _text_source()
    src.remove()
    sources.save(src)

    with pytest.raises(ValueError):
        provider.get_content(DocumentRefId(src.id.value))
