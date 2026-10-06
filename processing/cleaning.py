"""Pure text/price/rating/tag/URL cleaning helpers."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

_NBSP_PATTERN = re.compile(r"\u00a0|&nbsp;")
_WHITESPACE_PATTERN = re.compile(r"\s+")
_PRICE_PATTERN = re.compile(r"-?\d+(?:\.\d+)?")
_RATING_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}
_QUOTE_PAIRS = (
    ('"', '"'),
    ("'", "'"),
    ("“", "”"),
    ("‘", "’"),
)


def clean_text(value: object | None) -> str | None:
    """Normalize whitespace and return None for empty values."""
    if value is None:
        return None
    text = _NBSP_PATTERN.sub(" ", str(value))
    text = _WHITESPACE_PATTERN.sub(" ", text).strip()
    return text or None


def strip_quotes(value: object | None) -> str | None:
    """Remove surrounding straight or curly quotes after cleaning text."""
    text = clean_text(value)
    if text is None:
        return None

    changed = True
    while changed and text:
        changed = False
        for left, right in _QUOTE_PAIRS:
            if text.startswith(left) and text.endswith(right) and len(text) >= 2:
                text = text[len(left) : -len(right)].strip()
                changed = True
                break
    return text or None


def clean_price(value: object | None) -> float | None:
    """Extract a numeric price from strings such as '£51.77'."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).replace(",", "")
    match = _PRICE_PATTERN.search(text)
    if not match:
        return None
    return float(match.group())


def clean_rating(value: object | None) -> int | None:
    """Convert word ratings (One–Five) or integers 1–5 to an int."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if 1 <= value <= 5 else None
    if isinstance(value, float):
        if value.is_integer() and 1 <= int(value) <= 5:
            return int(value)
        return None

    text = clean_text(value)
    if text is None:
        return None

    lowered = text.lower()
    if lowered in _RATING_WORDS:
        return _RATING_WORDS[lowered]

    for token in re.split(r"[^a-z0-9]+", lowered):
        if token in _RATING_WORDS:
            return _RATING_WORDS[token]

    if text.isdigit():
        number = int(text)
        return number if 1 <= number <= 5 else None
    return None


def clean_tags(value: object | None) -> str | None:
    """Clean, lowercase, sort, and join tags with ';'."""
    if value is None or value == "":
        return None

    if isinstance(value, str):
        parts = re.split(r"[,;]", value)
    elif isinstance(value, (list, tuple, set)):
        parts = [str(item) for item in value]
    else:
        parts = [str(value)]

    normalized: list[str] = []
    seen: set[str] = set()
    for part in parts:
        tag = clean_text(part)
        if not tag:
            continue
        tag = tag.lower()
        if tag not in seen:
            seen.add(tag)
            normalized.append(tag)

    if not normalized:
        return None
    return ";".join(sorted(normalized))


def normalize_url(value: object | None, base_url: str | None = None) -> str | None:
    """Return an absolute http(s) URL, joining relative paths when a base is given."""
    text = clean_text(value)
    if text is None:
        return None
    if base_url:
        text = urljoin(base_url, text)

    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return text
