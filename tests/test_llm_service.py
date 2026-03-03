from __future__ import annotations

from types import SimpleNamespace

from app.services.llm_service import generate_answer


class MockOpenAI:
    def __init__(self, *args, **kwargs):
        message = SimpleNamespace(content="mocked answer")
        choice = SimpleNamespace(message=message)
        completion = SimpleNamespace(choices=[choice])
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **_: completion))


def test_generate_answer(monkeypatch) -> None:
    monkeypatch.setattr("app.services.llm_service.OpenAI", MockOpenAI)
    answer = generate_answer("What is this?", [{"text": "context"}])
    assert answer == "mocked answer"
