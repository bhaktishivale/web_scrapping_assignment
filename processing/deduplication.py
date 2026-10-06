"""Deterministic duplicate detection using SHA-256 fingerprints."""

from __future__ import annotations

import hashlib
import re

from processing.schema import SOURCE_BOOKS, SOURCE_QUOTES

_PUNCTUATION = re.compile(r"[^\w\s]+", flags=re.UNICODE)
_WHITESPACE = re.compile(r"\s+")


def normalize_identifying(value: object | None) -> str:
    """Lowercase, strip punctuation, and collapse whitespace for hashing."""
    if value is None:
        return ""
    text = str(value).lower()
    text = _PUNCTUATION.sub(" ", text)
    text = _WHITESPACE.sub(" ", text).strip()
    return text


def record_fingerprint(record: dict) -> str:
    """Build a stable fingerprint from source-specific identifying fields."""
    source = normalize_identifying(record.get("source"))
    title = normalize_identifying(record.get("name_or_title"))
    original_source = record.get("source")

    if original_source == SOURCE_BOOKS:
        payload = f"{source}|{title}"
    elif original_source == SOURCE_QUOTES:
        author = normalize_identifying(record.get("author"))
        payload = f"{source}|{author}|{title[:50]}"
    else:
        payload = f"{source}|{title}|{normalize_identifying(record.get('author'))}"

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def deduplicate_records(records: list[dict]) -> tuple[list[dict], list[dict]]:
    """Return (unique_records, duplicate_records) keeping first occurrence."""
    unique: list[dict] = []
    duplicates: list[dict] = []
    seen: set[str] = set()

    for record in records:
        fingerprint = record_fingerprint(record)
        if fingerprint in seen:
            duplicates.append(record)
        else:
            seen.add(fingerprint)
            unique.append(record)
    return unique, duplicates
