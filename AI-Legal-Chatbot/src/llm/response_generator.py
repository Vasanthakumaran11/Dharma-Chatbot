from __future__ import annotations

from typing import Any

from src.retrieval.similarity_search import search_similar_chunks
from src.retrieval.prompt_builder import (
    build_rag_prompt,
    build_system_prompt,
    apply_legal_disclaimer,
)
from src.llm.ollama_client import generate, chat, is_ollama_available


# ---------------------------------------------------------------------------
# Fallback response when Ollama is unavailable
# ---------------------------------------------------------------------------

_OLLAMA_UNAVAILABLE_MSG = (
    "⚠️ **Dharma is currently in offline mode.**\n\n"
    "The AI response engine (Ollama) is not reachable. "
    "Please make sure Ollama is running with a model loaded:\n\n"
    "```\nollama serve\nollama pull llama3\n```\n\n"
    "In the meantime, here are the relevant legal sections I found for your query:\n\n"
)


def _format_fallback_sources(chunks: list[dict[str, Any]]) -> str:
    """Format retrieved chunks as a readable list when LLM is unavailable."""
    if not chunks:
        return "No relevant legal provisions found."
    lines = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        law = meta.get("law_name", "Unknown Law")
        section = meta.get("section_number", "")
        title = meta.get("section_title", "")
        text = chunk.get("text", "")[:400]
        lines.append(f"**{i}. {law}**" + (f" — Section {section}" if section else ""))
        if title:
            lines.append(f"*{title}*")
        lines.append(f"> {text}...")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main response entry point
# ---------------------------------------------------------------------------

def get_answer_with_sources(
    query: str,
    history: list[dict[str, str]],
    index,
    metadata: list[dict[str, Any]],
    embedding_model,
    intent: str | None = None,
    top_k: int = 5,
    law_filter: str | None = None,
) -> dict[str, Any]:
    """
    Full RAG pipeline: retrieve → prompt → generate → return answer + sources.

    Parameters
    ----------
    query           : The user's current message.
    history         : List of previous turns [{role, content}].
    index           : Pre-loaded FAISS index.
    metadata        : Pre-loaded chunk metadata list.
    embedding_model : SentenceTransformer encoder.
    intent          : Detected intent category (optional).
    top_k           : Number of chunks to retrieve.
    law_filter      : Filter results to a specific law (optional).

    Returns
    -------
    Dict with:
        - answer (str)
        - sources (list of chunk metadata dicts)
        - retrieved_chunks (list of full chunk records)
        - ollama_available (bool)
    """
    # 1. Retrieve relevant legal chunks
    retrieved_chunks = search_similar_chunks(
        query=query,
        index=index,
        metadata=metadata,
        model=embedding_model,
        top_k=top_k,
        law_filter=law_filter,
    )

    # Build source citation list for the UI
    sources = []
    for chunk in retrieved_chunks:
        meta = chunk.get("metadata", {})
        sources.append(
            {
                "law_name": meta.get("law_name", ""),
                "law_short": meta.get("law_short", ""),
                "section_number": meta.get("section_number", ""),
                "section_title": meta.get("section_title", ""),
                "chapter_title": meta.get("chapter_title", ""),
                "legal_domain": meta.get("legal_domain", ""),
                "score": round(chunk.get("score", 0.0), 4),
            }
        )

    # 2. Check if Ollama is reachable
    if not is_ollama_available():
        fallback_answer = _OLLAMA_UNAVAILABLE_MSG + _format_fallback_sources(retrieved_chunks)
        return {
            "answer": fallback_answer,
            "sources": sources,
            "retrieved_chunks": retrieved_chunks,
            "ollama_available": False,
        }

    # 3. Build RAG prompt
    prompt = build_rag_prompt(
        query=query,
        retrieved_chunks=retrieved_chunks,
        history=history,
        intent=intent,
    )

    # 4. Generate answer via Ollama
    try:
        raw_answer = generate(prompt=prompt, temperature=0.25, max_tokens=1500)
        answer = apply_legal_disclaimer(raw_answer)
    except RuntimeError as exc:
        answer = (
            f"⚠️ **Error generating response**: {exc}\n\n"
            + _OLLAMA_UNAVAILABLE_MSG
            + _format_fallback_sources(retrieved_chunks)
        )
        return {
            "answer": answer,
            "sources": sources,
            "retrieved_chunks": retrieved_chunks,
            "ollama_available": False,
        }

    return {
        "answer": answer,
        "sources": sources,
        "retrieved_chunks": retrieved_chunks,
        "ollama_available": True,
    }
