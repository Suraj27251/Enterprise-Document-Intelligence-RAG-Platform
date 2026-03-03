from __future__ import annotations

from pathlib import Path

from app.services.embeddings import chunk_text, load_documents


def test_chunk_text_overlap() -> None:
    tokens = " ".join([f"t{i}" for i in range(1000)])
    chunks = chunk_text(tokens, chunk_size=200, overlap=50)
    assert len(chunks) > 1
    first = chunks[0].split()
    second = chunks[1].split()
    assert first[-50:] == second[:50]


def test_load_documents_reads_txt(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_text("hello world", encoding="utf-8")

    docs = load_documents(tmp_path)
    assert len(docs) == 1
    assert docs[0]["text"] == "hello world"
