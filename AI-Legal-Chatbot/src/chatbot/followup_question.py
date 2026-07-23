from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Field-to-question mapping
# ---------------------------------------------------------------------------

_FIELD_QUESTIONS: dict[str, str] = {
    "incident_location": "📍 Where did the incident occur? (city, state, or specific location)",
    "incident_date": "📅 When did the incident happen? (approximate date and time)",
    "item_stolen": "📦 What was stolen? (please describe the item and its approximate value)",
    "platform_used": "💻 Which platform or app was used in the fraud? (e.g., WhatsApp, UPI, email)",
    "amount_lost": "💰 How much money was lost or involved?",
    "relationship_to_accused": "👤 What is the accused person's relationship to you? (e.g., spouse, family member)",
    "vehicle_type": "🚗 What type of vehicle(s) were involved in the accident?",
    "product_or_service": "🛍️ What product or service are you complaining about?",
    "company_name": "🏢 What is the name of the company or seller?",
    "purchase_date": "🗓️ When did you make the purchase?",
    "missing_person_name": "🙋 What is the name of the missing person?",
    "last_seen_location": "📍 Where was the person last seen?",
    "last_seen_date": "📅 When were they last seen?",
    "public_authority_name": "🏛️ Which public authority or government department did you contact?",
    "information_sought": "📄 What information are you seeking through RTI?",
    "incident_type": "🗂️ Could you briefly describe the type of incident you want to report?",
    "witness_available": "👀 Were there any witnesses to the incident?",
    "evidence_available": "🗂️ Do you have any evidence such as photos, videos, or documents?",
    "fir_filed": "📋 Have you already filed an FIR with the police?",
}

# Suggested follow-up questions by intent category
_INTENT_FOLLOWUPS: dict[str, list[str]] = {
    "theft": ["incident_location", "incident_date", "item_stolen", "fir_filed"],
    "cybercrime": ["platform_used", "incident_date", "amount_lost", "evidence_available"],
    "domestic_violence": ["incident_location", "relationship_to_accused", "witness_available"],
    "traffic_accident": ["incident_location", "incident_date", "vehicle_type", "fir_filed"],
    "consumer_dispute": ["product_or_service", "company_name", "purchase_date"],
    "missing_person": ["missing_person_name", "last_seen_location", "last_seen_date"],
    "rti": ["public_authority_name", "information_sought"],
    "general_complaint": ["incident_type", "incident_location", "incident_date"],
    "general": ["incident_type"],
}


# ---------------------------------------------------------------------------
# Follow-up logic
# ---------------------------------------------------------------------------

def get_missing_fields(
    intent: str,
    collected_fields: dict[str, str],
) -> list[str]:
    """Return the list of required fields that haven't been collected yet."""
    required = _INTENT_FOLLOWUPS.get(intent, [])
    return [f for f in required if f not in collected_fields]


def get_next_followup_question(
    intent: str,
    collected_fields: dict[str, str],
) -> str | None:
    """
    Return the next follow-up question to ask the user, or None if all
    required information has been collected.
    """
    missing = get_missing_fields(intent, collected_fields)
    if not missing:
        return None
    next_field = missing[0]
    return _FIELD_QUESTIONS.get(next_field)


def extract_field_from_response(
    field_name: str,
    user_message: str,
) -> str | None:
    """
    Simple heuristic to extract a field value from user's reply.
    Returns the user's full message as the answer (the field is just acknowledged).
    """
    if len(user_message.strip()) > 3:
        return user_message.strip()
    return None


def should_ask_followup(
    intent: str,
    collected_fields: dict[str, str],
    turn_count: int,
) -> bool:
    """
    Decide whether to ask a follow-up question or proceed with answering.
    We only ask follow-ups during the first 3 turns to avoid being annoying.
    """
    if turn_count > 3:
        return False
    missing = get_missing_fields(intent, collected_fields)
    return len(missing) > 0


def format_followup_response(question: str, intent_label: str) -> str:
    """Wrap a follow-up question in a friendly response format."""
    return (
        f"I understand you're dealing with a **{intent_label}** matter. "
        f"To give you the most accurate legal guidance, I need a little more information.\n\n"
        f"{question}"
    )
