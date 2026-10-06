from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper

BOOKS_HTML = """
<html>
  <body>
    <article class="product_pod">
      <h3><a href="catalogue/a-light-in-the-attic_1000/index.html" title="A Light in the Attic">A Light in the ...</a></h3>
      <p class="star-rating Three"></p>
      <p class="price_color">£51.77</p>
    </article>
    <article class="product_pod">
      <h3><a href="catalogue/broken.html">Broken</a></h3>
    </article>
    <ul class="pager">
      <li class="next"><a href="catalogue/page-2.html">next</a></li>
    </ul>
  </body>
</html>
"""

QUOTES_HTML = """
<html>
  <body>
    <div class="quote">
      <span class="text">“The world as we have created it is a process of our thinking.”</span>
      <small class="author">Albert Einstein</small>
      <div class="tags">
        <a class="tag" href="/tag/change/page/1/">change</a>
        <a class="tag" href="/tag/deep-thoughts/page/1/">deep-thoughts</a>
      </div>
    </div>
    <ul class="pager">
      <li class="next"><a href="/page/2/">next</a></li>
    </ul>
  </body>
</html>
"""

LAST_PAGE_HTML = """
<html>
  <body>
    <div class="quote"><span class="text">Last</span><small class="author">Anon</small></div>
  </body>
</html>
"""


def test_books_parser_uses_title_attribute_and_survives_partial_cards() -> None:
    soup = BeautifulSoup(BOOKS_HTML, "lxml")
    records = BooksScraper().parse_records(soup, "https://books.toscrape.com/")
    assert len(records) == 2
    assert records[0]["name_or_title"] == "A Light in the Attic"
    assert records[0]["price"] == "£51.77"
    assert records[0]["rating"] == "Three"
    assert records[0]["source_url"].endswith("a-light-in-the-attic_1000/index.html")
    assert records[0]["category"] is None
    assert records[0]["description"] is None


def test_quotes_parser_and_dynamic_next_link() -> None:
    scraper = QuotesScraper()
    soup = BeautifulSoup(QUOTES_HTML, "lxml")
    records = scraper.parse_records(soup, "https://quotes.toscrape.com/")
    assert len(records) == 1
    assert "world as we have created it" in records[0]["name_or_title"]
    assert records[0]["author"] == "Albert Einstein"
    assert records[0]["tags"] == ["change", "deep-thoughts"]
    assert records[0]["source_url"] == "https://quotes.toscrape.com/"
    assert (
        scraper.next_page_url(soup, "https://quotes.toscrape.com/")
        == "https://quotes.toscrape.com/page/2/"
    )


def test_pagination_stops_when_next_is_missing() -> None:
    soup = BeautifulSoup(LAST_PAGE_HTML, "lxml")
    assert BaseScraper().next_page_url(soup, "https://quotes.toscrape.com/page/10/") is None
