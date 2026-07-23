from __future__ import annotations

import os

import torch
from sentence_transformers import SentenceTransformer

# bge-small-en-v1.5: 33M params, 384-dim, ~10x faster than large on CPU,
# excellent retrieval quality for legal/domain text.
# Override with EMBEDDING_MODEL env var if you want the larger model.
_DEFAULT_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")


def load_embedding_model(model_name: str | None = None, device: str | None = None):
    """Load a Sentence Transformers encoder for legal chunk embeddings."""
    model_name = model_name or _DEFAULT_MODEL
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"Loading embedding model '{model_name}' on {device}...")
    model = SentenceTransformer(model_name, device=device)
    return model
