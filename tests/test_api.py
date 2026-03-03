from __future__ import annotations

from app.core.security import create_access_token


def test_healthcheck(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_auth_token(client) -> None:
    response = client.post("/api/v1/auth/token", json={"username": "alice", "role": "Admin"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_search_requires_auth(client) -> None:
    response = client.get("/api/v1/search", params={"query": "hello"})
    assert response.status_code == 403


def test_search_with_auth(monkeypatch, client) -> None:
    monkeypatch.setattr("app.api.endpoints.retrieve_similar_chunks", lambda query, top_k=5: [{"source": "a", "chunk_id": 0, "text": "ctx", "score": 0.1}])
    monkeypatch.setattr("app.api.endpoints.generate_answer", lambda user_query, retrieved_chunks: "ok")

    token = create_access_token(username="bob", role="User")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/search", params={"query": "hello"}, headers=headers)

    assert response.status_code == 200
    assert response.json()["answer"] == "ok"


def test_root_route(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Enterprise Document Intelligence API" in response.text
    assert '/docs' in response.text


def test_version_route(client) -> None:
    response = client.get("/version")
    assert response.status_code == 200
    payload = response.json()
    assert "commit" in payload
    assert "service" in payload


def test_404_payload_includes_links(client) -> None:
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    payload = response.json()
    assert payload["docs"] == "/docs"
    assert payload["version"] == "/version"
