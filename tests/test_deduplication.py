from processing.deduplication import deduplicate_records, record_fingerprint
from processing.schema import SOURCE_BOOKS, SOURCE_QUOTES


def _book(title: str) -> dict:
    return {
        "source": SOURCE_BOOKS,
        "source_url": "https://books.toscrape.com/catalogue/example/index.html",
        "name_or_title": title,
        "author": None,
    }


def _quote(text: str, author: str = "Jane Austen") -> dict:
    return {
        "source": SOURCE_QUOTES,
        "source_url": "https://quotes.toscrape.com/",
        "name_or_title": text,
        "author": author,
    }


def test_exact_duplicate() -> None:
    unique, duplicates = deduplicate_records(
        [_book("Example Book Title"), _book("Example Book Title")]
    )
    assert len(unique) == 1
    assert len(duplicates) == 1


def test_case_and_whitespace_duplicates() -> None:
    unique, duplicates = deduplicate_records(
        [
            _book("Example Book Title"),
            _book(" Example Book Title "),
            _book("EXAMPLE BOOK TITLE"),
        ]
    )
    assert len(unique) == 1
    assert len(duplicates) == 2
    assert record_fingerprint(_book("Example Book Title")) == record_fingerprint(
        _book(" EXAMPLE BOOK TITLE ")
    )


def test_punctuation_differences() -> None:
    unique, duplicates = deduplicate_records(
        [_book("Example Book Title"), _book("Example Book Title!")]
    )
    assert len(unique) == 1
    assert len(duplicates) == 1


def test_different_records_remain_unique() -> None:
    unique, duplicates = deduplicate_records(
        [_book("Example Book Title"), _book("A Completely Different Title")]
    )
    assert len(unique) == 2
    assert duplicates == []


def test_quote_fingerprint_uses_author_and_prefix() -> None:
    first = _quote("It is a truth universally acknowledged that a single man")
    second = _quote("It is a truth universally acknowledged that a single man extra")
    unique, duplicates = deduplicate_records([first, second])
    assert len(unique) == 1
    assert len(duplicates) == 1

    different_author = _quote(
        "It is a truth universally acknowledged that a single man",
        author="Someone Else",
    )
    unique, duplicates = deduplicate_records([first, different_author])
    assert len(unique) == 2
    assert duplicates == []
