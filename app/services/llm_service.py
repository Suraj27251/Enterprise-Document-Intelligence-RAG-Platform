"""LLM integration for final RAG answer synthesis."""

from __future__ import annotations

import logging
from typing import Sequence

from openai import OpenAI

from app.core.config import get_settings
from app.core.prompt_utils import build_rag_prompt

logger = logging.getLogger(__name__)


def generate_answer(user_query: str, retrieved_chunks: Sequence[dict[str, str | int | float]]) -> str:
    """Generate answer using OpenAI ChatCompletion with contextual RAG prompt."""

    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    context = [str(chunk.get("text", "")).strip() for chunk in retrieved_chunks]
    prompt = build_rag_prompt(user_query, context)

    completion = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": "You are an enterprise document intelligence assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )

    answer = completion.choices[0].message.content or "No response generated."
    logger.info("Generated answer for query of length %s", len(user_query))
    return answer
