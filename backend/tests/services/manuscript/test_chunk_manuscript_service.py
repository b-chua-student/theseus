# tests/services/manuscript/test_chunk_manuscript.py
from uuid import uuid4

from ports.chunking.chonkie_chunker import ChonkieChunker
from domain.manuscript.aggregates import Manuscript
from services.manuscript.chunk_manuscript import ChunkManuscriptService


def build_manuscript() -> Manuscript:
    manuscript = Manuscript(id=uuid4(), project_id=uuid4(), title="Thesis")

    intro = manuscript.add_section(
        "Introduction",
        "<h2>Background</h2><p>" + "Climate models rely on sparse data. " * 30 + "</p>",
    )
    manuscript.add_section(
        "Methods",
        "<p>" + "We sampled sites across three regions. " * 30 + "</p>",
        parent_id=intro.id,
    )
    manuscript.add_section("Conclusion", "<p>Short closing note.</p>")

    return manuscript


def test_chunk_manuscript_prints_output() -> None:
    service = ChunkManuscriptService(chunker=ChonkieChunker(chunk_size=64))
    manuscript = build_manuscript()

    result = service.execute(manuscript)

    print(f"\nManuscript: {result.title}")
    for section in manuscript.sections:
        section_chunks = result.chunks[section.id]
        print(f"\nSection: {section.heading.value} ({len(section_chunks)} chunks)")
        for index, chunk in enumerate(section_chunks):
            print(f"  [{index}] tokens={chunk.token_count} text={chunk.text!r}")

    assert set(result.chunks) == {section.id for section in manuscript.sections}
    assert all(len(chunks) >= 1 for chunks in result.chunks.values())
