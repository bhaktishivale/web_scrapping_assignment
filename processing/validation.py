"""Record-level validation that never raises for bad data."""

from __future__ import annotations

from processing.schema import ALLOWED_SOURCES


def validate_record(record: dict | None) -> list[str]:
    """Return reason codes for problems; an empty list means the record is valid."""
    if not isinstance(record, dict):
        return ["invalid_record"]

    reasons: list[str] = []

    source = record.get("source")
    if source not in ALLOWED_SOURCES:
        reasons.append("unknown_source")

    name = record.get("name_or_title")
    if name is None or (isinstance(name, str) and not name.strip()):
        reasons.append("missing_name")

    url = record.get("source_url")
    if not isinstance(url, str) or not (
        url.startswith("http://") or url.startswith("https://")
    ):
        reasons.append("invalid_url")

    price = record.get("price")
    if price is not None and price != "":
        if isinstance(price, bool) or not isinstance(price, (int, float)):
            reasons.append("invalid_price")
        elif price < 0:
            reasons.append("invalid_price")

    rating = record.get("rating")
    if rating is not None and rating != "":
        if isinstance(rating, bool) or not isinstance(rating, int) or not 1 <= rating <= 5:
            reasons.append("invalid_rating")

    return reasons
