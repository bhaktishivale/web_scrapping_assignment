"""Shared schema constants for the consolidated dataset."""

from __future__ import annotations

from typing import Final

SOURCE_BOOKS: Final[str] = "Books to Scrape"
SOURCE_QUOTES: Final[str] = "Quotes to Scrape"

ALLOWED_SOURCES: Final[frozenset[str]] = frozenset({SOURCE_BOOKS, SOURCE_QUOTES})

CSV_FIELDNAMES: Final[list[str]] = [
    "source",
    "source_url",
    "name_or_title",
    "category",
    "price",
    "rating",
    "author",
    "tags",
    "description",
    "scraped_at",
]
