from uuid import UUID, uuid4

import pytest

from domain.indexing.aggregates import IndexedDocument
from domain.indexing.value_objects import (
    EmbeddingModelRef,
    IndexStatus,
    OwnerKind,
)
from ports.chunking.chunker import Chunk
from repositories.indexing.indexed_document_repository import (
    IndexedDocumentRepository,
)
from services.indexing.create_indexed_document import CreateIndexedDocumentService
from services.manuscript.chunk_manuscript import ChunkedManuscript


class FakeIndexedDocumentRepository(IndexedDocumentRepository):
    """Records saved documents for assertions."""

    def __init__(self) -> None:
        self.saved: list[IndexedDocument] = []

    def save(self, indexed_document: IndexedDocument) -> None:
        self.saved.append(indexed_document)


def make_chunk(text: str, start: int = 0, end: int = 10) -> Chunk:
    return Chunk(text=text, start_index=start, end_index=end, token_count=len(text.split()))


def make_chunked_manuscript(
    chunks: dict[UUID, list[Chunk]],
    manuscript_id: UUID | None = None,
) -> ChunkedManuscript:
    return ChunkedManuscript(
        id=manuscript_id or uuid4(),
        project_id=uuid4(),
        title="Thesis",
        chunks=chunks,
    )


MODEL = EmbeddingModelRef(name="gemini-embedding", version="1")


def test_creates_pending_document_for_manuscript() -> None:
    repo = FakeIndexedDocumentRepository()
    service = CreateIndexedDocumentService(repository=repo)
    manuscript_id = uuid4()
    chunked = make_chunked_manuscript({uuid4(): [make_chunk("alpha")]}, manuscript_id)

    result = service.execute(chunked, MODEL)

    assert result.owner_kind is OwnerKind.MANUSCRIPT
    assert result.owner_id == manuscript_id
    assert result.status is IndexStatus.PENDING
    assert result.model == MODEL


def test_persists_document_once() -> None:
    repo = FakeIndexedDocumentRepository()
    service = CreateIndexedDocumentService(repository=repo)
    chunked = make_chunked_manuscript({uuid4(): [make_chunk("alpha")]})

    result = service.execute(chunked, MODEL)

    assert repo.saved == [result]


def test_ordinals_are_global_across_sections() -> None:
    repo = FakeIndexedDocumentRepository()
    service = CreateIndexedDocumentService(repository=repo)
    first, second = uuid4(), uuid4()
    chunked = make_chunked_manuscript(
        {
            first: [make_chunk("a"), make_chunk("b")],
            second: [make_chunk("c")],
        }
    )

    result = service.execute(chunked, MODEL)

    assert [chunk.ordinal for chunk in result.chunks] == [0, 1, 2]
    assert [chunk.text for chunk in result.chunks] == ["a", "b", "c"]


def test_chunk_location_maps_section_and_indexes() -> None:
    repo = FakeIndexedDocumentRepository()
    service = CreateIndexedDocumentService(repository=repo)
    section_id = uuid4()
    chunked = make_chunked_manuscript({section_id: [make_chunk("a", start=5, end=42)]})

    result = service.execute(chunked, MODEL)

    location = result.chunks[0].location
    assert location.section_id == section_id
    assert location.start_index == 5
    assert location.end_index == 42


def test_chunks_reference_parent_document_id() -> None:
    repo = FakeIndexedDocumentRepository()
    service = CreateIndexedDocumentService(repository=repo)
    chunked = make_chunked_manuscript({uuid4(): [make_chunk("a"), make_chunk("b")]})

    result = service.execute(chunked, MODEL)

    assert all(
        chunk.indexed_document_id == result.indexed_document_id for chunk in result.chunks
    )


def test_content_hash_is_deterministic() -> None:
    repo = FakeIndexedDocumentRepository()
    service = CreateIndexedDocumentService(repository=repo)
    section_id = uuid4()
    chunks = {section_id: [make_chunk("same text")]}

    first = service.execute(make_chunked_manuscript(chunks), MODEL)
    second = service.execute(make_chunked_manuscript(chunks), MODEL)

    assert first.content_hash == second.content_hash


def test_content_hash_changes_when_text_changes() -> None:
    repo = FakeIndexedDocumentRepository()
    service = CreateIndexedDocumentService(repository=repo)
    section_id = uuid4()

    original = service.execute(
        make_chunked_manuscript({section_id: [make_chunk("before")]}), MODEL
    )
    edited = service.execute(
        make_chunked_manuscript({section_id: [make_chunk("after")]}), MODEL
    )

    assert original.content_hash != edited.content_hash


def test_manuscript_without_chunks_creates_empty_document() -> None:
    repo = FakeIndexedDocumentRepository()
    service = CreateIndexedDocumentService(repository=repo)

    result = service.execute(make_chunked_manuscript({}), MODEL)

    assert result.chunks == []
    assert len(repo.saved) == 1


def test_whitespace_only_chunk_is_rejected_and_not_saved() -> None:
    repo = FakeIndexedDocumentRepository()
    service = CreateIndexedDocumentService(repository=repo)
    chunked = make_chunked_manuscript({uuid4(): [make_chunk("   ")]})

    with pytest.raises(ValueError, match="Chunk text cannot be empty"):
        service.execute(chunked, MODEL)

    assert repo.saved == []
