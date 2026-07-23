from __future__ import annotations

import json
import os
from typing import Any, Iterator

import httpx

# Default Ollama endpoint — can be overridden via OLLAMA_HOST env var
_DEFAULT_HOST = "http://localhost:11434"
_DEFAULT_MODEL = "llama3"


def _get_host() -> str:
    return os.environ.get("OLLAMA_HOST", _DEFAULT_HOST).rstrip("/")


def _get_model() -> str:
    return os.environ.get("OLLAMA_MODEL", _DEFAULT_MODEL)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def is_ollama_available(timeout: float = 3.0) -> bool:
    """Return True if the Ollama server is reachable."""
    try:
        resp = httpx.get(f"{_get_host()}/api/tags", timeout=timeout)
        return resp.status_code == 200
    except Exception:
        return False


def list_available_models() -> list[str]:
    """Return the list of models available in the local Ollama instance."""
    try:
        resp = httpx.get(f"{_get_host()}/api/tags", timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def generate(
    prompt: str,
    model: str | None = None,
    system: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 1500,
    stream: bool = False,
    timeout: float = 300.0,
) -> str:
    """
    Call the Ollama /api/generate endpoint and return the response text.

    Parameters
    ----------
    prompt      : Full prompt string (already assembled).
    model       : Model name (defaults to OLLAMA_MODEL env var or 'llama3').
    system      : Optional system message (if sending separately).
    temperature : Sampling temperature (lower = more deterministic).
    max_tokens  : Maximum number of tokens to generate.
    stream      : If True, stream tokens (currently not used by caller).
    timeout     : HTTP timeout in seconds.

    Returns
    -------
    The generated text as a plain string.
    """
    model = model or _get_model()
    host = _get_host()

    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    if system:
        payload["system"] = system

    try:
        resp = httpx.post(
            f"{host}/api/generate",
            json=payload,
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()
    except httpx.ConnectError:
        raise RuntimeError(
            "Cannot connect to Ollama. Make sure Ollama is running "
            f"at {host}. Run: ollama serve"
        )
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Ollama returned an error: {exc.response.status_code} {exc.response.text}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"Unexpected error calling Ollama: {exc}") from exc


def chat(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 1500,
    timeout: float = 300.0,
) -> str:
    """
    Call the Ollama /api/chat endpoint using the messages API.

    Parameters
    ----------
    messages : List of dicts with 'role' (system/user/assistant) and 'content'.
    """
    model = model or _get_model()
    host = _get_host()

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }

    try:
        resp = httpx.post(
            f"{host}/api/chat",
            json=payload,
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "").strip()
    except httpx.ConnectError:
        raise RuntimeError(
            "Cannot connect to Ollama. Make sure Ollama is running "
            f"at {host}. Run: ollama serve"
        )
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Ollama returned an error: {exc.response.status_code} {exc.response.text}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"Unexpected error calling Ollama: {exc}") from exc
