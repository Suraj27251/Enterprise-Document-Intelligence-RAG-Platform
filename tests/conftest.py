from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def sample_vector_store(tmp_path: Path) -> Path:
    vector_dir = tmp_path / "vector_store"
    vector_dir.mkdir(parents=True)

    vectors = np.array([[0.1, 0.2, 0.3], [0.1, 0.2, 0.4]], dtype="float32")
    index = faiss.IndexFlatL2(3)
    index.add(vectors)
    faiss.write_index(index, str(vector_dir / "index.faiss"))

    metadata = [
        {"source": "doc_contract.txt", "chunk_id": 0, "text": "contract terms and pricing"},
        {"source": "doc_sla.txt", "chunk_id": 1, "text": "service level agreement details"},
    ]
    (vector_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    return vector_dir
