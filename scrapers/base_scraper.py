"""Shared HTTP session, retries, pagination, and request logging."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; AssignmentScraper/1.0; "
    "+https://books.toscrape.com/; educational-use)"
)


@dataclass
class ScrapeResult:
    """Outcome of scraping one source, including page-level stats."""

    records: list[dict] = field(default_factory=list)
    pages_ok: int = 0
    pages_failed: int = 0
    error: str | None = None


class BaseScraper:
    """Reusable HTTP client with polite delays and limited retries."""

    start_url: str = ""
    source_name: str = ""

    def __init__(
        self,
        delay_seconds: float = 0.5,
        timeout_seconds: float = 15.0,
        max_retries: int = 3,
        session: requests.Session | None = None,
    ) -> None:
        self.delay_seconds = delay_seconds
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", DEFAULT_USER_AGENT)
        self._last_request_at: float | None = None

    def _respect_rate_limit(self) -> None:
        if self._last_request_at is None:
            return
        elapsed = time.monotonic() - self._last_request_at
        remaining = self.delay_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def fetch(self, url: str) -> str | None:
        """GET a URL with timeout, retries, and backoff for temporary failures."""
        last_error: Exception | str | None = None

        for attempt in range(self.max_retries + 1):
            self._respect_rate_limit()
            try:
                response = self.session.get(url, timeout=self.timeout_seconds)
                self._last_request_at = time.monotonic()

                if response.status_code in RETRY_STATUS_CODES:
                    last_error = f"HTTP {response.status_code}"
                    logger.warning(
                        "Temporary HTTP failure for %s (%s), attempt %s/%s",
                        url,
                        response.status_code,
                        attempt + 1,
                        self.max_retries + 1,
                    )
                    if attempt < self.max_retries:
                        time.sleep(2**attempt)
                        continue
                    logger.error("Giving up on %s after HTTP %s", url, response.status_code)
                    return None

                if response.status_code >= 400:
                    logger.error(
                        "Request failed for %s with HTTP %s",
                        url,
                        response.status_code,
                    )
                    return None

                return response.text
            except requests.RequestException as exc:
                self._last_request_at = time.monotonic()
                last_error = exc
                logger.warning(
                    "Request exception for %s: %s (attempt %s/%s)",
                    url,
                    exc,
                    attempt + 1,
                    self.max_retries + 1,
                )
                if attempt < self.max_retries:
                    time.sleep(2**attempt)
                    continue
                logger.error("Giving up on %s after exception: %s", url, exc)
                return None

        logger.error("Failed to fetch %s: %s", url, last_error)
        return None

    def next_page_url(self, soup: BeautifulSoup, current_url: str) -> str | None:
        """Follow li.next > a dynamically; never assume a page count."""
        link = soup.select_one("li.next > a")
        if link is None:
            return None
        href = link.get("href")
        if not href:
            return None
        return urljoin(current_url, href)

    def parse_records(self, soup: BeautifulSoup, page_url: str) -> list[dict]:
        raise NotImplementedError

    def scrape(self) -> ScrapeResult:
        """Walk next-links from start_url until pagination ends."""
        result = ScrapeResult()
        url: str | None = self.start_url

        while url:
            logger.info("Requesting page: %s", url)
            html = self.fetch(url)
            if html is None:
                result.pages_failed += 1
                logger.error("Failed to process page: %s", url)
                break

            try:
                soup = BeautifulSoup(html, "lxml")
                page_records = self.parse_records(soup, url)
            except Exception:
                result.pages_failed += 1
                logger.exception("Unrecoverable parse failure for page: %s", url)
                break

            result.records.extend(page_records)
            result.pages_ok += 1
            logger.info(
                "Successfully processed page %s (%s records)",
                url,
                len(page_records),
            )
            url = self.next_page_url(soup, url)

        logger.info(
            "%s complete: %s records, %s pages ok, %s pages failed",
            self.source_name,
            len(result.records),
            result.pages_ok,
            result.pages_failed,
        )
        return result
