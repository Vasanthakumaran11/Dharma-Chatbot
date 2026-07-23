from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import faiss
import numpy as np


# ---------------------------------------------------------------------------
# Index / metadata loaders
# ---------------------------------------------------------------------------

def load_faiss_index(index_path: Path | str | None = None) -> faiss.Index:
    """Load a FAISS index from disk."""
    if index_path is None:
        project_root = Path(__file__).resolve().parents[2]
        index_path = project_root / "data" / "vector_db" / "legal_index.faiss"
    index_path = Path(index_path)
    if not index_path.exists():
        raise FileNotFoundError(
            f"FAISS index not found at {index_path}. "
            "Run build_vector_db.py first to generate the index."
        )
    return faiss.read_index(str(index_path))


def load_metadata_payload(metadata_path: Path | str | None = None) -> list[dict[str, Any]]:
    """Load the chunk metadata payload from the pickle file."""
    if metadata_path is None:
        project_root = Path(__file__).resolve().parents[2]
        metadata_path = project_root / "data" / "vector_db" / "chunks_metadata.pkl"
    metadata_path = Path(metadata_path)
    if not metadata_path.exists():
        raise FileNotFoundError(
            f"Metadata payload not found at {metadata_path}. "
            "Run build_vector_db.py first."
        )
    with metadata_path.open("rb") as fh:
        records = pickle.load(fh)
    return records


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def search_similar_chunks(
    query: str,
    index: faiss.Index,
    metadata: list[dict[str, Any]],
    model,
    top_k: int = 5,
    law_filter: str | None = None,
    topic_filter: str | None = None,
) -> list[dict[str, Any]]:
    """
    Encode *query* and perform similarity search against the FAISS index.

    Parameters
    ----------
    query       : Natural-language question from the user.
    index       : Pre-loaded FAISS index.
    metadata    : List of chunk records (from load_metadata_payload).
    model       : SentenceTransformer encoder (already loaded).
    top_k       : Number of results to return (before optional filtering).
    law_filter  : If provided, only chunks whose ``law_short`` contains this
                  string (case-insensitive) are returned.
    topic_filter: If provided, filter on ``topics`` or ``legal_domain`` fields.

    Returns
    -------
    List of dicts, each with keys ``text``, ``metadata``, and ``score``.
    """
    # Encode query
    query_embedding: np.ndarray = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype(np.float32)

    # Search — retrieve extra results so filtering doesn't starve results
    search_k = min(top_k * 4, index.ntotal)
    distances, indices = index.search(query_embedding, search_k)

    results: list[dict[str, Any]] = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0 or idx >= len(metadata):
            continue
        record = metadata[idx]
        meta = record.get("metadata", {})

        # Optional law filter
        if law_filter:
            law_short = str(meta.get("law_short", "")).lower()
            law_name = str(meta.get("law_name", "")).lower()
            if law_filter.lower() not in law_short and law_filter.lower() not in law_name:
                continue

        # Optional topic filter
        if topic_filter:
            topics = " ".join(meta.get("topics", [])).lower()
            domain = str(meta.get("legal_domain", "")).lower()
            if topic_filter.lower() not in topics and topic_filter.lower() not in domain:
                continue

        results.append(
            {
                "text": record.get("text", ""),
                "metadata": meta,
                "score": float(dist),
            }
        )

        if len(results) >= top_k:
            break

    return results
