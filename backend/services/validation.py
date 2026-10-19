from services.groq_service import LLMError

SEVERITY_LEVELS = ("high", "medium", "low")


def clamp_score(value, low: int = 0, high: int = 50) -> int:
    """Coerce an LLM-provided score to an int within [low, high]."""
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError):
        raise LLMError(f"LLM returned a non-numeric score: {value!r}")
    return max(low, min(high, score))


def normalize_level(value) -> str:
    """Map an LLM-provided severity/impact to high/medium/low."""
    level = str(value or "").strip().lower()
    return level if level in SEVERITY_LEVELS else "low"


def require_list_of_dicts(data: dict, key: str) -> list:
    """Return data[key] as a list of dicts, dropping malformed entries."""
    items = data.get(key, [])
    if not isinstance(items, list):
        raise LLMError(f"LLM returned '{key}' that is not a list")
    return [item for item in items if isinstance(item, dict)]
