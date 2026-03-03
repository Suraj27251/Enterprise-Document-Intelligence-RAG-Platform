from __future__ import annotations

from types import SimpleNamespace

from app.services.retriever import retrieve_similar_chunks


class MockOpenAI:
    def __init__(self, *args, **kwargs):
        self.embeddings = SimpleNamespace(
            create=lambda **_: SimpleNamespace(data=[SimpleNamespace(embedding=[0.1, 0.2, 0.3])])
        )


def test_retrieve_similar_chunks(monkeypatch, sample_vector_store) -> None:
    monkeypatch.setattr("app.services.retriever.OpenAI", MockOpenAI)
    results = retrieve_similar_chunks("contract info", top_k=1, store_dir=sample_vector_store)
    assert len(results) == 1
    assert "source" in results[0]
    assert "text" in results[0]
