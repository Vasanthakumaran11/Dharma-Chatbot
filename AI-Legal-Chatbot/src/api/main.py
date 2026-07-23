from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on the path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import src.chatbot.chatbot as chatbot_module
from src.embedding.embedding_model import load_embedding_model
from src.embedding.build_vector_db import load_chunks
from src.retrieval.similarity_search import load_faiss_index, load_metadata_payload
from src.llm.ollama_client import is_ollama_available, list_available_models


# ---------------------------------------------------------------------------
# Application lifespan — load resources once at startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load FAISS index, metadata, and embedding model at startup."""
    print("[START] Dharma Chatbot API starting up...")

    try:
        print("  Loading FAISS index...")
        index = load_faiss_index()
        print(f"  [OK] FAISS index loaded ({index.ntotal} vectors)")
    except FileNotFoundError as exc:
        print(f"  [WARN] FAISS index not found: {exc}")
        print("  Run: python -m src.embedding.build_vector_db to build it.")
        index = None

    try:
        print("  Loading metadata payload...")
        metadata = load_metadata_payload()
        print(f"  [OK] Metadata loaded ({len(metadata)} chunks)")
    except FileNotFoundError as exc:
        print(f"  [WARN] Metadata not found: {exc}")
        metadata = []

    print("  Loading embedding model (BAAI/bge-small-en-v1.5)...")
    embedding_model = load_embedding_model()
    print(f"  [OK] Embedding model loaded")

    if index is not None and metadata:
        chatbot_module.initialize(index, metadata, embedding_model)
        print("  [OK] Chatbot initialized successfully")
    else:
        print("  [WARN] Chatbot running in limited mode (no vector index)")

    ollama_up = is_ollama_available()
    print(f"  Ollama: {'available' if ollama_up else 'not available (offline mode)'}")
    if ollama_up:
        models = list_available_models()
        print(f"  Available models: {models}")

    print("[READY] Dharma API is ready!")
    yield
    print("[STOP] Dharma API shutting down...")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Dharma Legal Chatbot API",
    description="AI-powered legal guidance assistant for Indian police complaint procedures.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., min_length=1, max_length=2000, description="User's message")


class SourceCitation(BaseModel):
    law_name: str
    law_short: str
    section_number: str
    section_title: str
    chapter_title: str
    legal_domain: str
    score: float


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[SourceCitation]
    intent: str
    intent_label: str
    is_followup: bool
    turn_count: int
    ollama_available: bool


class HealthResponse(BaseModel):
    status: str
    chatbot_initialized: bool
    ollama_available: bool
    available_models: list[str]
    total_vectors: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint to verify API and dependencies status."""
    ollama_up = is_ollama_available()
    models = list_available_models() if ollama_up else []
    total_vectors = 0
    try:
        idx = load_faiss_index()
        total_vectors = idx.ntotal
    except Exception:
        pass

    return HealthResponse(
        status="ok",
        chatbot_initialized=chatbot_module.is_initialized(),
        ollama_available=ollama_up,
        available_models=models,
        total_vectors=total_vectors,
    )


@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Process a user message and return an AI-generated legal guidance response.
    """
    if not chatbot_module.is_initialized():
        raise HTTPException(
            status_code=503,
            detail=(
                "The chatbot is not fully initialized. "
                "The FAISS index may not have been built yet. "
                "Run: python -m src.embedding.build_vector_db"
            ),
        )

    try:
        result = chatbot_module.process_message(
            session_id=request.session_id,
            user_message=request.message,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(
        session_id=result["session_id"],
        answer=result["answer"],
        sources=[SourceCitation(**s) for s in result.get("sources", [])],
        intent=result.get("intent", "general"),
        intent_label=result.get("intent_label", "General Query"),
        is_followup=result.get("is_followup", False),
        turn_count=result.get("turn_count", 0),
        ollama_available=result.get("ollama_available", True),
    )


@app.get("/api/session/{session_id}", tags=["Session"])
async def get_session(session_id: str):
    """Retrieve the full conversation history for a session."""
    info = chatbot_module.get_session_history(session_id)
    return info


@app.delete("/api/session/{session_id}", tags=["Session"])
async def delete_session(session_id: str):
    """Clear a session and reset its conversation history."""
    chatbot_module.reset_session(session_id)
    return {"message": f"Session {session_id} has been cleared."}


@app.get("/", tags=["System"])
async def root():
    return {
        "name": "Dharma Legal Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }
