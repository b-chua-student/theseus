from ports.chunking.chonkie_chunker import ChonkieChunker


def test_chunk_prints_output() -> None:
    chunker = ChonkieChunker(chunk_size=16)
    text = "The quick brown fox jumps over the lazy dog. " * 50

    chunks = chunker.chunk(text)

    for chunk in chunks:
        print(chunk)

    assert len(chunks) > 1
