from processing.schema import SOURCE_BOOKS
from processing.validation import validate_record


def _valid_book() -> dict:
    return {
        "source": SOURCE_BOOKS,
        "source_url": "https://books.toscrape.com/catalogue/example/index.html",
        "name_or_title": "Example Book Title",
        "category": None,
        "price": 12.5,
        "rating": 4,
        "author": None,
        "tags": None,
        "description": None,
        "scraped_at": "2026-01-01T00:00:00+00:00",
    }


def test_valid_record() -> None:
    assert validate_record(_valid_book()) == []


def test_missing_name() -> None:
    record = _valid_book()
    record["name_or_title"] = "  "
    assert "missing_name" in validate_record(record)


def test_invalid_url() -> None:
    record = _valid_book()
    record["source_url"] = "ftp://example.com/book"
    assert "invalid_url" in validate_record(record)


def test_invalid_price() -> None:
    record = _valid_book()
    record["price"] = -1
    assert "invalid_price" in validate_record(record)
    record["price"] = "12.50"
    assert "invalid_price" in validate_record(record)


def test_invalid_rating() -> None:
    record = _valid_book()
    record["rating"] = 6
    assert "invalid_rating" in validate_record(record)
    record["rating"] = 4.0
    assert "invalid_rating" in validate_record(record)


def test_unknown_source() -> None:
    record = _valid_book()
    record["source"] = "Some Other Site"
    assert "unknown_source" in validate_record(record)
