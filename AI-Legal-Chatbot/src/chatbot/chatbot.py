from __future__ import annotations

from typing import Any

from src.chatbot.conversation_memory import (
    get_or_create_session,
    add_turn,
    get_history,
    get_intent,
    set_intent,
    get_fields,
    set_field,
    get_session_info,
    clear_session,
)
from src.chatbot.intent_classifier import classify_intent, get_intent_label
from src.chatbot.followup_question import (
    get_next_followup_question,
    format_followup_response,
    should_ask_followup,
    extract_field_from_response,
    get_missing_fields,
)
from src.llm.response_generator import get_answer_with_sources


# ---------------------------------------------------------------------------
# Global shared resources (loaded once at startup)
# ---------------------------------------------------------------------------

_index = None
_metadata = None
_embedding_model = None


def initialize(index, metadata: list[dict], embedding_model) -> None:
    """
    Initialize the chatbot with pre-loaded FAISS index, metadata, and embedding model.
    Call this once at application startup.
    """
    global _index, _metadata, _embedding_model
    _index = index
    _metadata = metadata
    _embedding_model = embedding_model


def is_initialized() -> bool:
    return _index is not None and _metadata is not None and _embedding_model is not None


# ---------------------------------------------------------------------------
# Main message processor
# ---------------------------------------------------------------------------

def process_message(session_id: str, user_message: str) -> dict[str, Any]:
    """
    Process a user message and return a structured response.

    Parameters
    ----------
    session_id   : Unique session identifier.
    user_message : The user's natural-language input.

    Returns
    -------
    Dict with:
        - session_id (str)
        - answer (str): The chatbot's response
        - sources (list): Retrieved legal citations
        - intent (str): Detected or stored intent
        - intent_label (str): Human-readable intent
        - is_followup (bool): Whether this was a follow-up question
        - turn_count (int)
        - ollama_available (bool)
    """
    if not is_initialized():
        raise RuntimeError(
            "Chatbot is not initialized. Call chatbot.initialize(index, metadata, model) first."
        )

    # Ensure session exists
    session = get_or_create_session(session_id)
    turn_count = len(session.turns) // 2  # user+assistant pairs

    # Classify intent (use existing intent if already detected with confidence)
    intent_result = classify_intent(user_message)
    current_intent = intent_result["intent"]

    # If we already have a high-confidence intent, keep it
    stored_intent = get_intent(session_id)
    if stored_intent and stored_intent != "general" and current_intent == "general":
        current_intent = stored_intent
        intent_result["intent"] = stored_intent
        intent_result["label"] = get_intent_label(stored_intent)
    elif current_intent != "general":
        set_intent(session_id, current_intent)

    # Collect fields from the user's message if we're in follow-up mode
    collected_fields = get_fields(session_id)
    missing_fields = get_missing_fields(current_intent, collected_fields)
    if missing_fields and turn_count > 0:
        # Try to store the current message as the answer to the last missing field
        last_missing = missing_fields[0]
        extracted = extract_field_from_response(last_missing, user_message)
        if extracted:
            set_field(session_id, last_missing, extracted)
            collected_fields = get_fields(session_id)  # refresh

    # Store user turn
    add_turn(session_id, "user", user_message)

    # Decide: ask follow-up or generate full answer?
    followup_q = get_next_followup_question(current_intent, collected_fields)

    if followup_q and should_ask_followup(current_intent, collected_fields, turn_count):
        answer = format_followup_response(followup_q, intent_result["label"])
        add_turn(session_id, "assistant", answer)
        return {
            "session_id": session_id,
            "answer": answer,
            "sources": [],
            "intent": current_intent,
            "intent_label": intent_result["label"],
            "is_followup": True,
            "turn_count": turn_count + 1,
            "ollama_available": True,
        }

    # Build enriched query with collected context
    enriched_query = _enrich_query(user_message, current_intent, collected_fields)

    # Generate answer via RAG
    history = get_history(session_id, max_turns=8)
    law_filter = intent_result.get("law_hint")

    result = get_answer_with_sources(
        query=enriched_query,
        history=history,
        index=_index,
        metadata=_metadata,
        embedding_model=_embedding_model,
        intent=current_intent,
        top_k=5,
        law_filter=None,  # broad retrieval across all laws for best coverage
    )

    answer = result["answer"]
    add_turn(session_id, "assistant", answer)

    return {
        "session_id": session_id,
        "answer": answer,
        "sources": result["sources"],
        "intent": current_intent,
        "intent_label": intent_result["label"],
        "is_followup": False,
        "turn_count": turn_count + 1,
        "ollama_available": result.get("ollama_available", True),
    }


def get_session_history(session_id: str) -> dict[str, Any]:
    """Return full session info for the API."""
    return get_session_info(session_id)


def reset_session(session_id: str) -> None:
    """Clear a session."""
    clear_session(session_id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _enrich_query(
    user_message: str,
    intent: str,
    collected_fields: dict[str, str],
) -> str:
    """Enrich the user query with collected context for better retrieval."""
    if not collected_fields:
        return user_message

    context_parts = []
    if loc := collected_fields.get("incident_location"):
        context_parts.append(f"Location: {loc}")
    if date := collected_fields.get("incident_date"):
        context_parts.append(f"Date: {date}")
    if item := collected_fields.get("item_stolen"):
        context_parts.append(f"Item: {item}")
    if platform := collected_fields.get("platform_used"):
        context_parts.append(f"Platform: {platform}")

    if not context_parts:
        return user_message

    context_str = "; ".join(context_parts)
    return f"{user_message} [{context_str}]"
