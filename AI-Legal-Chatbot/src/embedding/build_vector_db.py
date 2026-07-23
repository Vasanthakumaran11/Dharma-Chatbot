from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path
from typing import Any

import faiss
import numpy as np

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.embedding.embedding_model import load_embedding_model


def load_chunks(metadata_dir: Path | None = None, chunks_dir: Path | None = None) -> list[dict[str, Any]]:
    """Load legal chunk metadata records and attach their source text from the chunk files."""
    project_root = Path(__file__).resolve().parents[2]
    metadata_dir = metadata_dir or project_root / "data" / "metadata"
    chunks_dir = chunks_dir or project_root / "data" / "chunks"

    metadata_dir = Path(metadata_dir)
    chunks_dir = Path(chunks_dir)

    if not metadata_dir.exists():
        raise FileNotFoundError(f"Metadata directory not found: {metadata_dir}")

    if not chunks_dir.exists():
        raise FileNotFoundError(f"Chunk directory not found: {chunks_dir}")

    metadata_files = sorted(metadata_dir.glob("*.json"))
    if not metadata_files:
        raise FileNotFoundError(f"No metadata JSON files were found in {metadata_dir}")

    records: list[dict[str, Any]] = []
    print(f"Found {len(metadata_files)} metadata file(s). Loading chunk texts...")

    for metadata_path in metadata_files:
        print(f"  - Reading {metadata_path.name}")
        with metadata_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if isinstance(payload, dict):
            metadata_records = payload.get("chunks", payload.get("records", []))
        else:
            metadata_records = payload

        if not isinstance(metadata_records, list):
            raise ValueError(f"Expected a list of records in {metadata_path}")

        chunk_source_name = metadata_path.stem.replace("_metadata", "") + ".json"
        chunk_path = chunks_dir / chunk_source_name
        if not chunk_path.exists():
            raise FileNotFoundError(f"Matching chunk file not found: {chunk_path}")

        with chunk_path.open("r", encoding="utf-8") as handle:
            chunk_payload = json.load(handle)

        chunk_texts = {}
        for chunk in chunk_payload.get("chunks", []):
            section_number = str(chunk.get("section_number") or "").strip()
            if section_number:
                chunk_texts[section_number] = chunk.get("text", "")

        for item in metadata_records:
            if not isinstance(item, dict):
                continue

            section_number = str(item.get("section_number") or "").strip()
            text = chunk_texts.get(section_number, item.get("text", ""))
            if not text:
                text = " ".join(
                    filter(
                        None,
                        [
                            item.get("section_title", ""),
                            item.get("chapter_title", ""),
                            item.get("law_name", ""),
                        ],
                    )
                )

            records.append(
                {
                    "text": text,
                    "metadata": {
                        **item,
                        "document": chunk_payload.get("document", item.get("law_name", "")),
                        "source_file": chunk_payload.get("source_file", ""),
                    },
                }
            )

    print(f"Loaded {len(records)} legal chunks for embedding.")
    return records


def generate_embeddings(records: list[dict[str, Any]], model, batch_size: int = 32) -> np.ndarray:
    """Generate dense embeddings for the provided chunk records in batches."""
    if not records:
        raise ValueError("No records available for embedding generation")

    texts = [record["text"] for record in records]
    print(f"Generating embeddings for {len(texts)} chunks using batch size {batch_size}...")

    embeddings_list: list[np.ndarray] = []
    total = len(texts)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch_texts = texts[start:end]
        print(f"  Encoding batch {start // batch_size + 1}/{(total + batch_size - 1) // batch_size} ({end - start} chunks)...")
        batch_embeddings = model.encode(
            batch_texts,
            batch_size=len(batch_texts),
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        if batch_embeddings.ndim == 1:
            batch_embeddings = np.expand_dims(batch_embeddings, axis=0)
        embeddings_list.append(np.asarray(batch_embeddings, dtype=np.float32))

    embeddings = np.vstack(embeddings_list)
    print(f"Generated embeddings shape: {embeddings.shape}")
    return embeddings


def build_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    """Build a FAISS index for semantic retrieval."""
    if embeddings.ndim != 2:
        raise ValueError("Embeddings must be a 2D array")

    dimension = embeddings.shape[1]
    print(f"Building FAISS index with dimension {dimension}...")
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    return index


def save_index(index: faiss.Index, records: list[dict[str, Any]], output_dir: Path | None = None) -> tuple[Path, Path]:
    """Persist the FAISS index and the metadata payload to disk."""
    project_root = Path(__file__).resolve().parents[2]
    output_dir = output_dir or project_root / "data" / "vector_db"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    index_path = output_dir / "legal_index.faiss"
    metadata_path = output_dir / "chunks_metadata.pkl"

    print(f"Saving FAISS index to {index_path}...")
    faiss.write_index(index, str(index_path))

    print(f"Saving chunk metadata payload to {metadata_path}...")
    with metadata_path.open("wb") as handle:
        pickle.dump(records, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return index_path, metadata_path


def main() -> None:
    """End-to-end embedding generation pipeline for the legal chunk corpus."""
    print("Starting legal embedding pipeline...")

    records = load_chunks()
    model = load_embedding_model()
    embeddings = generate_embeddings(records, model)
    index = build_faiss_index(embeddings)
    save_index(index, records)

    print("Embedding pipeline completed successfully.")


if __name__ == "__main__":
    main()
