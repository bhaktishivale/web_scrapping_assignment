from processing.cleaning import (
    clean_price,
    clean_rating,
    clean_tags,
    clean_text,
    normalize_url,
    strip_quotes,
)


def test_clean_text_collapses_whitespace_and_nbsp() -> None:
    assert clean_text("  Hello\u00a0  world\n") == "Hello world"


def test_clean_text_none_and_empty() -> None:
    assert clean_text(None) is None
    assert clean_text("   ") is None


def test_strip_quotes_straight_and_curly() -> None:
    assert strip_quotes('"Hello"') == "Hello"
    assert strip_quotes("“Hello”") == "Hello"


def test_clean_price_currency_and_commas() -> None:
    assert clean_price("£51.77") == 51.77
    assert clean_price("$1,234.50") == 1234.50


def test_clean_price_invalid() -> None:
    assert clean_price("not a price") is None
    assert clean_price(None) is None


def test_clean_rating_words() -> None:
    assert clean_rating("One") == 1
    assert clean_rating("Two") == 2
    assert clean_rating("Three") == 3
    assert clean_rating("Four") == 4
    assert clean_rating("Five") == 5
    assert clean_rating("star-rating Three") == 3


def test_clean_rating_invalid() -> None:
    assert clean_rating("Zero") is None
    assert clean_rating(9) is None


def test_clean_tags_normalize_sort_and_join() -> None:
    assert clean_tags([" Humor ", "life", "HUMOR"]) == "humor;life"


def test_normalize_url_absolute_and_relative() -> None:
    assert (
        normalize_url("https://quotes.toscrape.com/page/2/")
        == "https://quotes.toscrape.com/page/2/"
    )
    assert (
        normalize_url("catalogue/page-2.html", "https://books.toscrape.com/")
        == "https://books.toscrape.com/catalogue/page-2.html"
    )
    assert normalize_url("not-a-url") is None
