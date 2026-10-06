"""ETL entry point: scrape, clean, validate, deduplicate, and write outputs."""

from __future__ import annotations

import csv
import json
import logging
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from processing.deduplication import deduplicate_records
from processing.records import clean_record
from processing.schema import CSV_FIELDNAMES, SOURCE_BOOKS, SOURCE_QUOTES
from processing.validation import validate_record
from scrapers.base_scraper import ScrapeResult
from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output"
LOG_DIR = ROOT / "logs"
CSV_PATH = OUTPUT_DIR / "final_dataset.csv"
SUMMARY_PATH = OUTPUT_DIR / "summary_report.json"
LOG_PATH = LOG_DIR / "scraper.log"

logger = logging.getLogger("pipeline")


class UtcFormatter(logging.Formatter):
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    formatter = UtcFormatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(file_handler)
    root.addHandler(console_handler)


def run_source(name: str, scraper) -> ScrapeResult:
    try:
        return scraper.scrape()
    except Exception as exc:
        logger.exception("Unrecoverable failure while scraping %s", name)
        return ScrapeResult(error=str(exc))


def empty_row() -> str:
    return ""


def csv_row(record: dict) -> dict:
    row = {}
    for field in CSV_FIELDNAMES:
        value = record.get(field)
        row[field] = empty_row() if value is None else value
    return row


def write_csv(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        for record in records:
            writer.writerow(csv_row(record))


def write_json(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def process_source_records(source_name: str, raw_records: list[dict]) -> dict:
    cleaned = [clean_record(raw) for raw in raw_records]
    valid: list[dict] = []
    rejected = 0
    reasons: Counter[str] = Counter()

    for record in cleaned:
        problems = validate_record(record)
        if problems:
            rejected += 1
            reasons.update(problems)
            logger.warning(
                "Rejected %s record (%s): %s",
                source_name,
                ",".join(problems),
                record.get("name_or_title"),
            )
            continue
        valid.append(record)

    unique, duplicates = deduplicate_records(valid)
    for record in duplicates:
        logger.warning(
            "Duplicate %s record dropped: %s",
            source_name,
            record.get("name_or_title"),
        )
    return {
        "raw": len(raw_records),
        "cleaned": len(cleaned),
        "rejected": rejected,
        "rejection_reasons": dict(reasons),
        "duplicates": len(duplicates),
        "unique": unique,
    }


def main() -> int:
    configure_logging()
    started = datetime.now(timezone.utc)
    logger.info("Application start")

    books_result = run_source(SOURCE_BOOKS, BooksScraper())
    quotes_result = run_source(SOURCE_QUOTES, QuotesScraper())

    books_stats = process_source_records(SOURCE_BOOKS, books_result.records)
    quotes_stats = process_source_records(SOURCE_QUOTES, quotes_result.records)

    final_records = books_stats["unique"] + quotes_stats["unique"]
    write_csv(final_records, CSV_PATH)
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        csv_row_count = sum(1 for _ in csv.DictReader(handle))

    ended = datetime.now(timezone.utc)
    duration = (ended - started).total_seconds()
    total_duplicates = books_stats["duplicates"] + quotes_stats["duplicates"]
    rejection_reasons = dict(
        Counter(books_stats["rejection_reasons"]) + Counter(quotes_stats["rejection_reasons"])
    )

    summary = {
        "run_start_time": started.isoformat(),
        "run_end_time": ended.isoformat(),
        "duration_seconds": round(duration, 3),
        "raw_records": {
            SOURCE_BOOKS: books_stats["raw"],
            SOURCE_QUOTES: quotes_stats["raw"],
            "total": books_stats["raw"] + quotes_stats["raw"],
        },
        "cleaned_records": {
            SOURCE_BOOKS: books_stats["cleaned"],
            SOURCE_QUOTES: quotes_stats["cleaned"],
            "total": books_stats["cleaned"] + quotes_stats["cleaned"],
        },
        "rejected_records": {
            SOURCE_BOOKS: books_stats["rejected"],
            SOURCE_QUOTES: quotes_stats["rejected"],
            "total": books_stats["rejected"] + quotes_stats["rejected"],
        },
        "rejection_reasons": rejection_reasons,
        "duplicates": {
            SOURCE_BOOKS: books_stats["duplicates"],
            SOURCE_QUOTES: quotes_stats["duplicates"],
            "total": total_duplicates,
        },
        "final_record_count": len(final_records),
        "pages_successfully_processed": {
            SOURCE_BOOKS: books_result.pages_ok,
            SOURCE_QUOTES: quotes_result.pages_ok,
            "total": books_result.pages_ok + quotes_result.pages_ok,
        },
        "pages_failed": {
            SOURCE_BOOKS: books_result.pages_failed,
            SOURCE_QUOTES: quotes_result.pages_failed,
            "total": books_result.pages_failed + quotes_result.pages_failed,
        },
        "source_errors": {
            SOURCE_BOOKS: books_result.error,
            SOURCE_QUOTES: quotes_result.error,
        },
        "counts_reconcile": {
            "valid_equals_unique_plus_duplicates": (
                (books_stats["cleaned"] - books_stats["rejected"])
                == books_stats["duplicates"] + len(books_stats["unique"])
            )
            and (
                (quotes_stats["cleaned"] - quotes_stats["rejected"])
                == quotes_stats["duplicates"] + len(quotes_stats["unique"])
            ),
            "final_equals_csv_rows": len(final_records) == csv_row_count,
        },
        "output_files": {
            "csv": str(CSV_PATH),
            "summary": str(SUMMARY_PATH),
            "log": str(LOG_PATH),
        },
    }

    write_json(summary, SUMMARY_PATH)
    logger.info(
        "Final statistics: raw=%s cleaned=%s rejected=%s duplicates=%s final=%s duration_s=%s",
        summary["raw_records"]["total"],
        summary["cleaned_records"]["total"],
        summary["rejected_records"]["total"],
        total_duplicates,
        len(final_records),
        summary["duration_seconds"],
    )
    logger.info("Wrote %s and %s", CSV_PATH, SUMMARY_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
