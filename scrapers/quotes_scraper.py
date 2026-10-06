"""Scraper for https://quotes.toscrape.com/ listing pages."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from bs4 import BeautifulSoup, Tag

from processing.schema import SOURCE_QUOTES
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class QuotesScraper(BaseScraper):
    start_url = "https://quotes.toscrape.com/"
    source_name = SOURCE_QUOTES

    def parse_records(self, soup: BeautifulSoup, page_url: str) -> list[dict]:
        records: list[dict] = []
        quotes = soup.select("div.quote")
        if not quotes:
            logger.warning("No quote cards found on %s", page_url)

        for quote in quotes:
            try:
                record = self._parse_one(quote, page_url)
            except Exception:
                logger.warning("Skipping malformed quote record on %s", page_url, exc_info=True)
                continue
            if record is None:
                continue
            records.append(record)
        return records

    def _parse_one(self, quote: Tag, page_url: str) -> dict | None:
        text_el = quote.select_one("span.text")
        if text_el is None:
            logger.warning("Missing quote text on %s", page_url)
            return None

        author_el = quote.select_one("small.author")
        if author_el is None:
            logger.warning("Missing author on %s", page_url)
        author = author_el.get_text() if author_el else None

        tags = [tag.get_text() for tag in quote.select("a.tag")]
        scraped_at = datetime.now(timezone.utc).isoformat()

        # Quotes have no unique permalink; source_url is the listing page
        # where the quote was collected.
        return {
            "source": SOURCE_QUOTES,
            "source_url": page_url,
            "name_or_title": text_el.get_text(),
            "category": None,
            "price": None,
            "rating": None,
            "author": author,
            "tags": tags,
            "description": None,
            "scraped_at": scraped_at,
        }
