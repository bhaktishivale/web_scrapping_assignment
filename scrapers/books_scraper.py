"""Scraper for https://books.toscrape.com/ listing pages."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from processing.schema import SOURCE_BOOKS
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


def _rating_word(star_tag: Tag | None) -> str | None:
    if star_tag is None:
        return None
    classes = star_tag.get("class") or []
    for name in classes:
        if name.lower() != "star-rating":
            return str(name)
    return None


class BooksScraper(BaseScraper):
    start_url = "https://books.toscrape.com/"
    source_name = SOURCE_BOOKS

    def parse_records(self, soup: BeautifulSoup, page_url: str) -> list[dict]:
        records: list[dict] = []
        articles = soup.select("article.product_pod")
        if not articles:
            logger.warning("No book cards found on %s", page_url)

        for article in articles:
            try:
                record = self._parse_one(article, page_url)
            except Exception:
                logger.warning("Skipping malformed book record on %s", page_url, exc_info=True)
                continue
            if record is None:
                continue
            records.append(record)
        return records

    def _parse_one(self, article: Tag, page_url: str) -> dict | None:
        link = article.select_one("h3 > a")
        if link is None:
            logger.warning("Missing title link on %s", page_url)
            return None

        title = link.get("title") or link.get_text()
        href = link.get("href")
        if not href:
            logger.warning("Missing book href for %r on %s", title, page_url)
            return None

        price_el = article.select_one("p.price_color")
        if price_el is None:
            logger.warning("Missing price for %r on %s", title, page_url)
        price_raw = price_el.get_text() if price_el else None

        rating_raw = _rating_word(article.select_one("p.star-rating"))
        if rating_raw is None:
            logger.warning("Missing rating for %r on %s", title, page_url)

        # Listing pages do not include category or description; those stay empty.
        scraped_at = datetime.now(timezone.utc).isoformat()
        return {
            "source": SOURCE_BOOKS,
            "source_url": urljoin(page_url, href),
            "name_or_title": title,
            "category": None,
            "price": price_raw,
            "rating": rating_raw,
            "author": None,
            "tags": None,
            "description": None,
            "scraped_at": scraped_at,
        }
