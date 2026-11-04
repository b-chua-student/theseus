from uuid import uuid4

from domain.assistant.infrastructure.adapters.chroma_vector_store import ChromaVectorStore
from domain.assistant.models.value_objects import Chunk, ChunkId, DocumentRefId, Embedding


def _store() -> ChromaVectorStore:
    return ChromaVectorStore(collection_name=f"test_{uuid4().hex}")


def _chunk(text: str) -> Chunk:
    return Chunk(id=ChunkId.new(), text=text, position="0", location="p1", content_hash="h")


def _index(store: ChromaVectorStore, doc: DocumentRefId, items: list[tuple[str, list[float]]]):
    chunks = [_chunk(t) for t, _ in items]
    embs = [Embedding(c.id, v) for c, (_, v) in zip(chunks, items, strict=True)]
    store.upsert(doc, embs, chunks)
    return chunks


def test_query_returns_top_k_ordered() -> None:
    store, doc = _store(), DocumentRefId.new()
    _index(store, doc, [("x", [1.0, 0.0]), ("y", [0.0, 1.0]), ("xy", [0.7, 0.7])])
    res = store.query([1.0, 0.0], k=2)
    assert [r.text for r in res] == ["x", "xy"]
    assert res[0].score > res[1].score
    assert res[0].doc_ref_id == doc


def test_query_filters_by_document_and_delete() -> None:
    store, d1, d2 = _store(), DocumentRefId.new(), DocumentRefId.new()
    _index(store, d1, [("a", [1.0, 0.0])])
    _index(store, d2, [("b", [1.0, 0.1])])
    assert [r.text for r in store.query([1.0, 0.0], k=5, doc_ref_ids=[d2])] == ["b"]
    store.delete(d1)
    assert [r.text for r in store.query([1.0, 0.0], k=5)] == ["b"]


def test_upsert_replaces_and_empty_cases() -> None:
    store, doc = _store(), DocumentRefId.new()
    assert store.query([1.0, 0.0]) == []
    _index(store, doc, [("old", [1.0, 0.0])])
    _index(store, doc, [("new", [1.0, 0.0])])
    assert [r.text for r in store.query([1.0, 0.0], k=10)] == ["new"]
    assert store.query([1.0, 0.0], k=0) == []
    assert store.query([1.0, 0.0], doc_ref_ids=[]) == []
