"""Document loading, chunking, embedding generation, and FAISS persistence."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import faiss
import numpy as np
import pdfplumber
from openai import OpenAI
from PyPDF2 import PdfReader

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """In-memory representation of a chunk and its source metadata."""

    text: str
    source: str
    chunk_id: int


def load_documents(directory: str | Path) -> list[dict[str, str]]:
    """Read .txt and .pdf files from a directory and return text payloads."""

    directory_path = Path(directory)
    documents: list[dict[str, str]] = []

    for file_path in sorted(directory_path.glob("**/*")):
        if file_path.is_dir():
            continue

        if file_path.suffix.lower() == ".txt":
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            documents.append({"source": str(file_path), "text": text})
            logger.info("Loaded text file: %s", file_path)

        elif file_path.suffix.lower() == ".pdf":
            text = _read_pdf(file_path)
            documents.append({"source": str(file_path), "text": text})
            logger.info("Loaded PDF file: %s", file_path)

    return documents


def _read_pdf(file_path: Path) -> str:
    """Extract text from PDF using pdfplumber fallback to PyPDF2."""

    content_parts: list[str] = []

    try:
        with pdfplumber.open(file_path) as pdf:
            content_parts.extend((page.extract_text() or "") for page in pdf.pages)
    except Exception as exc:  # pragma: no cover - fallback protection
        logger.warning("pdfplumber failed for %s (%s), trying PyPDF2", file_path, exc)

    if not any(content_parts):
        reader = PdfReader(str(file_path))
        content_parts = [(page.extract_text() or "") for page in reader.pages]

    return "\n".join(part for part in content_parts if part)


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Chunk text by approximate token count using whitespace tokenization."""

    tokens = text.split()
    if not tokens:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunks.append(" ".join(tokens[start:end]))
        if end >= len(tokens):
            break
        start = max(end - overlap, 0)

    return chunks


def generate_embeddings(chunks: Iterable[DocumentChunk], model: str | None = None) -> tuple[list[list[float]], list[dict[str, str | int]]]:
    """Generate embeddings for chunks with OpenAI API."""

    settings = get_settings()
    model_name = model or settings.embedding_model
    client = OpenAI(api_key=settings.openai_api_key)

    vectors: list[list[float]] = []
    metadata: list[dict[str, str | int]] = []

    for chunk in chunks:
        response = client.embeddings.create(model=model_name, input=chunk.text)
        vector = response.data[0].embedding
        vectors.append(vector)
        metadata.append({"source": chunk.source, "chunk_id": chunk.chunk_id, "text": chunk.text})

    return vectors, metadata


def save_faiss_index(vectors: list[list[float]], metadata: list[dict[str, str | int]], output_dir: str | Path) -> None:
    """Persist vectors to FAISS and store metadata adjacent to index file."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if not vectors:
        raise ValueError("No vectors generated; cannot save FAISS index")

    dimension = len(vectors[0])
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(vectors, dtype="float32"))

    faiss.write_index(index, str(output_path / "index.faiss"))
    (output_path / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    logger.info("Saved FAISS index and metadata to %s", output_path)


def ingest_directory(directory: str | Path, output_dir: str | Path) -> int:
    """End-to-end ingestion helper; returns count of embedded chunks."""

    raw_docs = load_documents(directory)
    chunks: list[DocumentChunk] = []

    for doc in raw_docs:
        for chunk_id, text_chunk in enumerate(chunk_text(doc["text"])):
            chunks.append(DocumentChunk(text=text_chunk, source=doc["source"], chunk_id=chunk_id))

    vectors, metadata = generate_embeddings(chunks)
    save_faiss_index(vectors, metadata, output_dir)
    return len(chunks)
