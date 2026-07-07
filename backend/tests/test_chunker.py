from app.ingestion.chunker import chunk_text


def test_empty_text_returns_no_chunks() -> None:
    assert chunk_text("", source="empty.txt") == []
    assert chunk_text("   \n  ", source="whitespace.txt") == []


def test_text_smaller_than_chunk_size_is_single_chunk() -> None:
    chunks = chunk_text("short text", source="doc.txt", chunk_size=800, chunk_overlap=150)

    assert len(chunks) == 1
    assert chunks[0].text == "short text"
    assert chunks[0].source == "doc.txt"
    assert chunks[0].chunk_index == 0


def test_chunk_index_is_monotonic() -> None:
    text = " ".join(f"word{i}" for i in range(500))
    chunks = chunk_text(text, source="doc.txt", chunk_size=50, chunk_overlap=10)

    assert len(chunks) > 1
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_source_preserved_across_chunks() -> None:
    text = " ".join(f"word{i}" for i in range(500))
    chunks = chunk_text(text, source="report.pdf", chunk_size=50, chunk_overlap=10)

    assert all(c.source == "report.pdf" for c in chunks)


def test_respects_chunk_size_and_overlap() -> None:
    text = "a" * 1000
    chunks = chunk_text(text, source="doc.txt", chunk_size=100, chunk_overlap=20)

    assert all(len(c.text) <= 100 for c in chunks)
    # consecutive chunks should share overlapping content
    assert chunks[0].text[-20:] == chunks[1].text[:20]
