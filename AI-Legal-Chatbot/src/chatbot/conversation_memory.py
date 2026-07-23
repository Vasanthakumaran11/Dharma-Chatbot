from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ConversationTurn:
    role: str          # 'user' or 'assistant'
    content: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    session_id: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    turns: list[ConversationTurn] = field(default_factory=list)
    detected_intent: str | None = None
    collected_fields: dict[str, str] = field(default_factory=dict)


# Global in-memory session store
_sessions: dict[str, Session] = {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_session(session_id: str | None = None) -> str:
    """Create a new conversation session and return its ID."""
    sid = session_id or str(uuid.uuid4())
    _sessions[sid] = Session(session_id=sid)
    return sid


def get_session(session_id: str) -> Session | None:
    """Return a session object or None if not found."""
    return _sessions.get(session_id)


def get_or_create_session(session_id: str) -> Session:
    """Return existing session or create a fresh one."""
    if session_id not in _sessions:
        _sessions[session_id] = Session(session_id=session_id)
    return _sessions[session_id]


def add_turn(session_id: str, role: str, content: str, meta: dict | None = None) -> None:
    """Append a turn to the session history."""
    session = get_or_create_session(session_id)
    session.turns.append(
        ConversationTurn(role=role, content=content, metadata=meta or {})
    )


def get_history(session_id: str, max_turns: int = 10) -> list[dict[str, str]]:
    """Return the conversation history as a list of role/content dicts."""
    session = get_or_create_session(session_id)
    turns = session.turns[-max_turns:]
    return [{"role": t.role, "content": t.content} for t in turns]


def set_intent(session_id: str, intent: str) -> None:
    """Store the detected intent for a session."""
    session = get_or_create_session(session_id)
    session.detected_intent = intent


def get_intent(session_id: str) -> str | None:
    """Get the stored intent for a session."""
    session = get_or_create_session(session_id)
    return session.detected_intent


def set_field(session_id: str, field_name: str, value: str) -> None:
    """Store a collected conversation field (e.g., incident_location)."""
    session = get_or_create_session(session_id)
    session.collected_fields[field_name] = value


def get_fields(session_id: str) -> dict[str, str]:
    """Get all collected fields for a session."""
    session = get_or_create_session(session_id)
    return session.collected_fields


def clear_session(session_id: str) -> None:
    """Remove a session from memory."""
    _sessions.pop(session_id, None)


def list_sessions() -> list[str]:
    """Return all active session IDs."""
    return list(_sessions.keys())


def get_session_info(session_id: str) -> dict[str, Any]:
    """Return serializable session info for the API."""
    session = get_or_create_session(session_id)
    return {
        "session_id": session.session_id,
        "created_at": session.created_at,
        "turn_count": len(session.turns),
        "detected_intent": session.detected_intent,
        "collected_fields": session.collected_fields,
        "history": [
            {
                "role": t.role,
                "content": t.content,
                "timestamp": t.timestamp,
            }
            for t in session.turns
        ],
    }
