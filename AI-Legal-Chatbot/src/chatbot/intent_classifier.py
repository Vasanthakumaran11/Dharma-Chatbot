from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Intent definitions and keyword maps
# ---------------------------------------------------------------------------

INTENTS: dict[str, dict[str, Any]] = {
    "theft": {
        "label": "Theft / Robbery",
        "keywords": [
            "theft", "stolen", "robbed", "robbery", "pickpocket", "burglary",
            "snatching", "mobile stolen", "phone stolen", "wallet stolen",
            "house break", "vehicle theft", "bike stolen", "car stolen",
        ],
        "required_fields": ["incident_location", "incident_date", "item_stolen"],
        "law_hint": "BNS",
    },
    "cybercrime": {
        "label": "Cybercrime / Online Fraud",
        "keywords": [
            "cybercrime", "online fraud", "scam", "hacked", "phishing", "upi fraud",
            "otp fraud", "fake call", "cyber fraud", "online cheating", "social media hack",
            "account hacked", "bank fraud", "digital fraud", "internet fraud",
        ],
        "required_fields": ["incident_date", "platform_used", "amount_lost"],
        "law_hint": "IT Act",
    },
    "domestic_violence": {
        "label": "Domestic Violence",
        "keywords": [
            "domestic violence", "wife beating", "husband abuse", "dowry", "marital abuse",
            "family violence", "assault by spouse", "cruelty by husband", "matrimonial",
            "domestic abuse", "protection order", "women harassment at home",
        ],
        "required_fields": ["incident_location", "relationship_to_accused"],
        "law_hint": "BNS",
    },
    "traffic_accident": {
        "label": "Traffic Accident / Road Incident",
        "keywords": [
            "accident", "hit and run", "road accident", "car crash", "vehicle collision",
            "rash driving", "drunk driving", "traffic", "motor vehicle", "road rage",
            "injured in accident", "met with accident",
        ],
        "required_fields": ["incident_location", "incident_date", "vehicle_type"],
        "law_hint": "Motor Vehicles Act",
    },
    "consumer_dispute": {
        "label": "Consumer Dispute",
        "keywords": [
            "consumer complaint", "product defect", "faulty product", "refund denied",
            "service complaint", "e-commerce fraud", "amazon fraud", "flipkart",
            "consumer court", "consumer forum", "deficiency in service",
        ],
        "required_fields": ["product_or_service", "company_name", "purchase_date"],
        "law_hint": "Consumer Protection",
    },
    "missing_person": {
        "label": "Missing Person",
        "keywords": [
            "missing person", "child missing", "person missing", "lost child",
            "abducted", "kidnapping", "went missing", "disappeared", "not returning home",
        ],
        "required_fields": ["missing_person_name", "last_seen_location", "last_seen_date"],
        "law_hint": "BNSS",
    },
    "rti": {
        "label": "RTI / Government Transparency",
        "keywords": [
            "rti", "right to information", "government information", "public authority",
            "pio", "cic", "state information commission", "information not given",
            "application rejected", "government record",
        ],
        "required_fields": ["public_authority_name", "information_sought"],
        "law_hint": "RTI",
    },
    "general_complaint": {
        "label": "General Police Complaint",
        "keywords": [
            "file complaint", "lodge fir", "file fir", "police complaint", "how to report",
            "how to file", "what to do", "complaint procedure", "police station",
            "zero fir", "first information report",
        ],
        "required_fields": ["incident_type"],
        "law_hint": "BNSS",
    },
}

_THRESHOLD = 1  # minimum keyword matches for classification


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

def classify_intent(text: str) -> dict[str, Any]:
    """
    Classify the user's message into one of the supported legal intents.

    Returns
    -------
    Dict with:
        - intent (str): intent key or 'general'
        - label (str): human-readable label
        - confidence (float): 0.0–1.0
        - matched_keywords (list[str])
        - required_fields (list[str])
        - law_hint (str): suggested law filter for retrieval
        - needs_followup (bool)
    """
    text_lower = text.lower()

    scores: dict[str, int] = {}
    matched: dict[str, list[str]] = {}

    for intent_key, config in INTENTS.items():
        hits = [kw for kw in config["keywords"] if kw in text_lower]
        if hits:
            scores[intent_key] = len(hits)
            matched[intent_key] = hits

    if not scores:
        return _build_result("general", [], 0.0)

    best_intent = max(scores, key=scores.__getitem__)
    best_score = scores[best_intent]
    total_keywords = len(INTENTS[best_intent]["keywords"])
    confidence = min(1.0, best_score / max(3, total_keywords * 0.3))

    return _build_result(best_intent, matched.get(best_intent, []), confidence)


def _build_result(intent: str, keywords: list[str], confidence: float) -> dict[str, Any]:
    config = INTENTS.get(intent, {})
    required_fields = config.get("required_fields", [])
    return {
        "intent": intent,
        "label": config.get("label", "General Query"),
        "confidence": round(confidence, 3),
        "matched_keywords": keywords,
        "required_fields": required_fields,
        "law_hint": config.get("law_hint", None),
        "needs_followup": len(required_fields) > 0 and confidence > 0.2,
    }


def get_intent_label(intent_key: str) -> str:
    """Return human-readable label for an intent key."""
    return INTENTS.get(intent_key, {}).get("label", "General Query")
