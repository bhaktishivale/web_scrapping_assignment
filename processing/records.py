"""Apply cleaning functions to raw scraper records."""

from __future__ import annotations

from processing.cleaning import (
    clean_price,
    clean_rating,
    clean_tags,
    clean_text,
    normalize_url,
    strip_quotes,
)
from processing.schema import SOURCE_QUOTES


def clean_record(raw: dict) -> dict:
    """Return a schema-aligned record with cleaned field values."""
    name = raw.get("name_or_title")
    if raw.get("source") == SOURCE_QUOTES:
        name = strip_quotes(name)
    else:
        name = clean_text(name)

    return {
        "source": clean_text(raw.get("source")),
        "source_url": normalize_url(raw.get("source_url")),
        "name_or_title": name,
        "category": clean_text(raw.get("category")),
        "price": clean_price(raw.get("price")),
        "rating": clean_rating(raw.get("rating")),
        "author": clean_text(raw.get("author")),
        "tags": clean_tags(raw.get("tags")),
        "description": clean_text(raw.get("description")),
        "scraped_at": clean_text(raw.get("scraped_at")),
    }
