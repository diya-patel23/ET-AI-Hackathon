"""
Single shared LLM call path. Every agent and the RAG copilot import `call_llm`
from here instead of instantiating their own client. That means:
  - one place to swap models / providers
  - one place to add retries, timeouts, rate-limit handling
  - one place that degrades gracefully when no API key is configured, so the
    rest of the app (ingestion, search, graph, dashboard) still works and is
    demoable even before a key is added.

Supported providers (set LLM_PROVIDER in backend/.env):
  gemini  — Google Gemini API (needs GEMINI_API_KEY, subject to free quotas)
  ollama  — Local Ollama server (no key, no quota, fully offline)
             Install: https://ollama.com  |  pull model: ollama pull llama3.2
"""
import json
import logging
import re
import time
import urllib.error
import urllib.request

from app.config import GEMINI_API_KEY, LLM_MODEL, LLM_PROVIDER, OLLAMA_BASE_URL

logger = logging.getLogger("llm_client")

_RETRYABLE_STATUS_CODES = {429, 503}
_MAX_RETRIES = 3
_RETRY_BACKOFF_BASE = 2.0  # seconds; doubles each attempt

# ---------------------------------------------------------------------------
# Provider initialisation
# ---------------------------------------------------------------------------

_gemini_client = None
_provider = LLM_PROVIDER  # "gemini" | "ollama"

if _provider == "gemini":
    if GEMINI_API_KEY:
        try:
            from google import genai
            _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            logger.info("LLM provider: Gemini (model=%s)", LLM_MODEL)
        except Exception as e:  # pragma: no cover
            logger.warning("Could not initialise Gemini client: %s", e)
    else:
        logger.warning(
            "LLM_PROVIDER=gemini but GEMINI_API_KEY is not set. "
            "LLM features will return placeholders."
        )
elif _provider == "ollama":
    # Ollama uses a plain HTTP REST API — no SDK needed.
    # We do a quick connectivity check at startup so the log is informative.
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                logger.info(
                    "LLM provider: Ollama at %s (model=%s)", OLLAMA_BASE_URL, LLM_MODEL
                )
    except Exception as e:
        logger.warning(
            "Ollama server not reachable at %s — make sure `ollama serve` is running. "
            "Error: %s", OLLAMA_BASE_URL, e,
        )
else:
    logger.warning("Unknown LLM_PROVIDER=%r. Supported: 'gemini', 'ollama'.", _provider)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def llm_available() -> bool:
    """True when the configured provider looks usable."""
    if _provider == "gemini":
        return _gemini_client is not None
    if _provider == "ollama":
        # Considered available if the URL is set; a live check happens per-call.
        return bool(OLLAMA_BASE_URL)
    return False


# ---------------------------------------------------------------------------
# Internal — Gemini path
# ---------------------------------------------------------------------------

def _parse_retry_delay(err_str: str) -> float | None:
    """Extract the retryDelay value (seconds) the API suggests, if present."""
    m = re.search(r"retry[_ ]?(?:in|delay)[^\d]*(\d+(?:\.\d+)?)", err_str, re.IGNORECASE)
    return float(m.group(1)) if m else None


def _classify_error(err_str: str) -> str:
    """Return 'quota_daily' | 'rate_limit' | 'unavailable' | 'other'."""
    if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
        if "PerDay" in err_str or "per_day" in err_str.lower():
            return "quota_daily"
        return "rate_limit"
    if "UNAVAILABLE" in err_str or "503" in err_str:
        return "unavailable"
    return "other"


def _call_gemini(system: str, prompt: str, max_tokens: int) -> str:
    if not _gemini_client:
        return (
            "[LLM not configured] Set GEMINI_API_KEY in backend/.env to enable "
            "AI-generated answers and reports. Ingestion, search, and the "
            "knowledge graph work fully without it."
        )
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            resp = _gemini_client.models.generate_content(
                model=LLM_MODEL,
                contents=prompt,
                config={
                    "system_instruction": system,
                    "max_output_tokens": max_tokens,
                },
            )
            return (resp.text or "").strip()
        except Exception as e:  # pragma: no cover
            last_exc = e
            err_str = str(e)
            kind = _classify_error(err_str)

            if kind == "quota_daily":
                logger.error(
                    "LLM daily quota exhausted for model '%s'. "
                    "Switch to Ollama by setting LLM_PROVIDER=ollama in .env: %s",
                    LLM_MODEL, e,
                )
                return (
                    f"[LLM quota exhausted] The free-tier daily quota for "
                    f"'{LLM_MODEL}' has been reached. "
                    "Set LLM_PROVIDER=ollama in backend/.env to use a local model with no quota. "
                    "See https://ai.dev/rate-limit to monitor Gemini usage."
                )

            if kind in ("rate_limit", "unavailable") and attempt < _MAX_RETRIES - 1:
                wait = _parse_retry_delay(err_str) or (_RETRY_BACKOFF_BASE ** attempt)
                wait = min(wait, 30.0)
                logger.warning(
                    "LLM transient error (attempt %d/%d, kind=%s), retrying in %.1fs: %s",
                    attempt + 1, _MAX_RETRIES, kind, wait, e,
                )
                time.sleep(wait)
            else:
                break

    logger.error("LLM call failed after %d attempts: %s", _MAX_RETRIES, last_exc)
    return f"[LLM call failed: {last_exc}]"


# ---------------------------------------------------------------------------
# Internal — Ollama path
# ---------------------------------------------------------------------------

def _call_ollama(system: str, prompt: str, max_tokens: int) -> str:
    """Call the local Ollama /api/chat endpoint (OpenAI-compatible chat format)."""
    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {
            "num_predict": max_tokens,
        },
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            # /api/chat returns {"message": {"role": "assistant", "content": "..."}}
            return data.get("message", {}).get("content", "").strip()
        except urllib.error.URLError as e:
            last_exc = e
            if attempt < _MAX_RETRIES - 1:
                wait = _RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    "Ollama request failed (attempt %d/%d), retrying in %.1fs: %s",
                    attempt + 1, _MAX_RETRIES, wait, e,
                )
                time.sleep(wait)
            else:
                break
        except Exception as e:
            last_exc = e
            break

    logger.error("Ollama call failed after %d attempts: %s", _MAX_RETRIES, last_exc)
    return (
        f"[Ollama call failed: {last_exc}] "
        "Make sure `ollama serve` is running and the model is pulled: "
        f"`ollama pull {LLM_MODEL}`"
    )


# ---------------------------------------------------------------------------
# Public API — same interface as before; nothing else in the app changes
# ---------------------------------------------------------------------------

def call_llm(system: str, prompt: str, max_tokens: int = 1024) -> str:
    """Plain-text completion.

    Routes to the configured provider (Gemini or Ollama).
    Returns a clearly-labelled placeholder if nothing is configured, so
    callers can always render the result directly without crashing.
    """
    if _provider == "ollama":
        return _call_ollama(system, prompt, max_tokens)
    # default / gemini
    return _call_gemini(system, prompt, max_tokens)


def call_llm_json(system: str, prompt: str, max_tokens: int = 1024) -> dict | list | None:
    """Same as call_llm, but asks for JSON and parses it.

    Returns None on failure or when the LLM isn't configured, so callers
    can fall back to a rule-based path.

    Ollama (and other local models) often wrap their JSON response in markdown
    fences (```json ... ```) or add a preamble sentence before the JSON.
    This function extracts the first valid JSON object or array from anywhere
    in the response, so those stylistic variations don't cause silent failures.
    """
    if not llm_available():
        return None
    raw = call_llm(
        system + "\n\nRespond with ONLY valid JSON. No markdown fences, no preamble.",
        prompt,
        max_tokens=max_tokens,
    )

    # Strategy 1: try the whole response first (fast path for well-behaved models)
    try:
        return json.loads(raw.strip())
    except Exception:
        pass

    # Strategy 2: strip a single ```json ... ``` fence block
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except Exception:
            pass

    # Strategy 3: find the first { ... } or [ ... ] block anywhere in the text.
    # This catches responses where the model adds a preamble sentence before JSON.
    obj_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", raw)
    if obj_match:
        try:
            return json.loads(obj_match.group(1))
        except Exception:
            pass

    logger.warning("Failed to parse LLM JSON output — raw response: %s", raw[:400])
    return None

