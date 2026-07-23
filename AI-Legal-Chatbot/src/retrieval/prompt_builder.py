from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are Dharma, an AI legal guidance assistant specializing in Indian law and police complaint procedures.

Your role is to:
- Help users understand their legal rights under Indian law
- Explain police complaint procedures in simple, clear language
- Identify relevant laws and legal sections applicable to their situation
- Guide users on what evidence to preserve
- Explain the procedural steps they should follow
- Recommend what next actions to take

IMPORTANT LIMITATIONS — you must always follow these:
1. You are NOT a lawyer and cannot provide official legal advice.
2. Always recommend consulting a qualified lawyer for serious matters.
3. Base your answers STRICTLY on the retrieved legal context provided.
4. Do not fabricate or invent legal provisions. If unsure, say so.
5. Never impersonate a police officer, judge, or government authority.
6. Always include a brief disclaimer at the end of your response.

Response format:
- Use clear headings and bullet points.
- Mention the relevant law/section explicitly (e.g., "Under Section 154 of BNSS...").
- List the procedural steps numerically.
- End with a "⚠️ Legal Disclaimer" note.
"""

_LEGAL_DISCLAIMER = (
    "\n\n---\n"
    "⚠️ **Legal Disclaimer**: This information is for general guidance only and does not "
    "constitute legal advice. For your specific situation, please consult a qualified "
    "lawyer or visit your nearest Legal Services Authority (DLSA/SLSA)."
)


def build_system_prompt() -> str:
    """Return the full system prompt for the chatbot."""
    return _SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Context block builder
# ---------------------------------------------------------------------------

def build_retrieval_context_block(retrieved_chunks: list[dict[str, Any]]) -> str:
    """
    Format the retrieved legal chunks into a structured context block
    that will be injected into the RAG prompt.
    """
    if not retrieved_chunks:
        return "No specific legal provisions were retrieved for this query."

    lines: list[str] = ["=== RETRIEVED LEGAL CONTEXT ===\n"]
    for i, chunk in enumerate(retrieved_chunks, start=1):
        meta = chunk.get("metadata", {})
        law = meta.get("law_name", "Unknown Law")
        law_short = meta.get("law_short", "")
        section_num = meta.get("section_number", "")
        section_title = meta.get("section_title", "")
        chapter = meta.get("chapter_title", "")
        text = chunk.get("text", "").strip()
        score = chunk.get("score", 0.0)

        heading_parts = [f"[{i}]", law]
        if law_short and law_short != law:
            heading_parts.append(f"({law_short})")
        if section_num:
            heading_parts.append(f"— Section {section_num}")
        if section_title:
            heading_parts.append(f": {section_title}")

        lines.append(" ".join(heading_parts))
        if chapter:
            lines.append(f"    Chapter: {chapter}")
        lines.append(f"    Relevance score: {score:.3f}")
        lines.append(f"    Text: {text[:800]}")  # truncate very long chunks
        lines.append("")

    lines.append("=== END OF LEGAL CONTEXT ===")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# RAG prompt assembler
# ---------------------------------------------------------------------------

def build_rag_prompt(
    query: str,
    retrieved_chunks: list[dict[str, Any]],
    history: list[dict[str, str]] | None = None,
    intent: str | None = None,
) -> str:
    """
    Assemble the full RAG prompt from:
      - system instructions
      - conversation history (last N turns)
      - retrieved legal context
      - current user query
    """
    parts: list[str] = []

    # System prompt
    parts.append(_SYSTEM_PROMPT)
    parts.append("")

    # Detected intent context
    if intent and intent != "general":
        parts.append(f"Detected complaint category: {intent.upper()}")
        parts.append("")

    # Conversation history (keep last 6 turns to stay within context)
    if history:
        relevant_history = history[-6:]
        parts.append("=== CONVERSATION HISTORY ===")
        for turn in relevant_history:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            label = "User" if role == "user" else "Dharma"
            parts.append(f"{label}: {content}")
        parts.append("=== END OF HISTORY ===\n")

    # Retrieved legal context
    context_block = build_retrieval_context_block(retrieved_chunks)
    parts.append(context_block)
    parts.append("")

    # Current query
    parts.append(f"User's question: {query}")
    parts.append("")
    parts.append(
        "Based on the retrieved legal context above, provide a helpful, accurate, "
        "and structured response. Cite specific laws and sections. "
        "If the context does not contain enough information, say so honestly."
    )
    parts.append("Dharma:")

    return "\n".join(parts)


def apply_legal_disclaimer(answer: str) -> str:
    """Append the legal disclaimer to the answer if not already present."""
    if "Legal Disclaimer" in answer or "legal advice" in answer.lower():
        return answer
    return answer + _LEGAL_DISCLAIMER
