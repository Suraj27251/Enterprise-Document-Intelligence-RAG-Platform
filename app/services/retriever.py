"""Semantic retrieval utilities backed by FAISS."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import faiss
import numpy as np
from openai import OpenAI

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def retrieve_similar_chunks(query: str, top_k: int = 5, store_dir: str | Path | None = None) -> list[dict[str, str | int | float]]:
    """Retrieve top-k semantically similar chunks for a natural language query."""

    settings = get_settings()
    vector_dir = Path(store_dir or settings.vector_store_dir)
    index_path = vector_dir / "index.faiss"
    metadata_path = vector_dir / "metadata.json"

    if not index_path.exists() or not metadata_path.exists():
        logger.warning("Vector store not initialized at %s", vector_dir)
        return []

    index = faiss.read_index(str(index_path))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    client = OpenAI(api_key=settings.openai_api_key)
    embedding = client.embeddings.create(model=settings.embedding_model, input=query).data[0].embedding

    distances, indices = index.search(np.array([embedding], dtype="float32"), top_k)

    results: list[dict[str, str | int | float]] = []
    for rank, idx in enumerate(indices[0]):
        if idx < 0 or idx >= len(metadata):
            continue
        hit = metadata[idx]
        results.append(
            {
                "rank": rank + 1,
                "score": float(distances[0][rank]),
                "source": hit["source"],
                "chunk_id": hit["chunk_id"],
                "text": hit["text"],
            }
        )

    return results
