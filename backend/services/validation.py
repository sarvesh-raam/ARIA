import re

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


# Figures like 416,161 / 1,997.5 / 145.99 / 8268 — but not percentages (computed changes are fine)
FIGURE_PATTERN = re.compile(r"(?<![\d.,])(\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|\d+\.\d+|\d{3,})(?![\d,]*\.?\d*\s*%)")


def unsupported_figures(text: str, source: str) -> list[str]:
    """
    Figures quoted in LLM output that don't appear anywhere in the source excerpts.
    Catches invented or self-computed numbers (e.g. a "total debt" the model added up itself).
    """
    source_digits = {m.replace(",", "") for m in FIGURE_PATTERN.findall(source)}
    missing = []
    for figure in FIGURE_PATTERN.findall(text):
        plain = figure.replace(",", "")
        if re.fullmatch(r"(19|20)\d\d", plain):
            continue  # a year, not a figure
        if plain not in source_digits:
            missing.append(figure)
    return missing


def require_list_of_dicts(data: dict, key: str) -> list:
    """Return data[key] as a list of dicts, dropping malformed entries."""
    items = data.get(key, [])
    if not isinstance(items, list):
        raise LLMError(f"LLM returned '{key}' that is not a list")
    return [item for item in items if isinstance(item, dict)]
