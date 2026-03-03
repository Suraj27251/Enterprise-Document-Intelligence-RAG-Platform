"""Prompt utilities for assembling safe and consistent RAG prompts."""

from typing import Iterable


def format_context(chunks: Iterable[str]) -> str:
    """Render retrieved chunks in a consistent, numbered format."""

    cleaned = [chunk.strip() for chunk in chunks if chunk and chunk.strip()]
    if not cleaned:
        return "No relevant context retrieved."
    return "\n\n".join(f"[{idx + 1}] {chunk}" for idx, chunk in enumerate(cleaned))


def build_rag_prompt(question: str, context_chunks: Iterable[str]) -> str:
    """Build a canonical RAG prompt with system framing and context."""

    context_block = format_context(context_chunks)
    return (
        "System: You are an enterprise document intelligence assistant.\n"
        "Use only the provided context. If insufficient, state your uncertainty.\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question:\n{question.strip()}\n\n"
        "Answer:"
    )
