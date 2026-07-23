"""
Dharma Legal Chatbot — FastAPI entry point.

Run with:
    python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
"""
from src.api.main import app  # noqa: F401 — re-export for uvicorn
