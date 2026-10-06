# Web Scraping ETL Assignment

## 1. Project overview

This project is a small Python ETL pipeline. It scrapes two public practice websites, cleans and validates the records, removes duplicates, and writes one combined CSV plus a JSON summary report.

The websites are:

- https://books.toscrape.com/
- https://quotes.toscrape.com/

Both sites are designed for scraping practice. They are server-rendered HTML with no login wall.

## 2. Assignment objective

Build a complete, maintainable scraping pipeline that:

- scrapes **all** listing pages from both sites using dynamic pagination
- stores both sources in one standardized schema
- cleans, validates, and deduplicates records
- logs progress and failures
- writes `output/final_dataset.csv` and `output/summary_report.json`
- includes unit tests that do not need the internet

## 3. Technologies

- `requests` for HTTP
- `beautifulsoup4` with the `lxml` parser for HTML
- `pytest` for unit tests
- Python standard library: `csv`, `json`, `logging`, `re`, `urllib.parse`, `time`, `pathlib`, `hashlib`, `datetime`

Pandas is not used. CSV output is written with `csv.DictWriter`.

Requests + BeautifulSoup was selected instead of Selenium or Playwright because both practice sites return complete HTML from a normal GET request. There is no JavaScript rendering, login, or CAPTCHA to drive in a browser. A browser stack would be slower, harder to test, and unnecessary here.

## 4. Python version

The code is written for **Python 3.10–3.12**. It also runs on Python 3.9 because modules use `from __future__ import annotations`.

This machine's default interpreter during development was Anaconda Python 3.9.13.

## 5–7. Installation

From the project root:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS / Linux:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

`requirements.txt` pins:

- requests
- beautifulsoup4
- lxml
- pytest

## 8. How to run

```bash
python main.py
```

This scrapes both sites (about one minute with the 0.5 second delay), then writes:

- `output/final_dataset.csv`
- `output/summary_report.json`
- `logs/scraper.log`

Unit tests:

```bash
python -m pytest -q
```

Tests do not call the live websites.

## 9. Project structure

```text
web_scrapping_assignment/
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py
│   ├── books_scraper.py
│   └── quotes_scraper.py
├── processing/
│   ├── __init__.py
│   ├── schema.py
│   ├── cleaning.py
│   ├── validation.py
│   ├── deduplication.py
│   └── records.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_cleaning.py
│   ├── test_validation.py
│   ├── test_deduplication.py
│   └── test_scrapers.py
├── output/
│   ├── final_dataset.csv
│   └── summary_report.json
├── logs/
│   └── scraper.log
├── main.py
├── requirements.txt
├── README.md
├── AI_USAGE.md
└── INTERVIEW_NOTES.md
```

`processing/schema.py` holds the shared field list and allowed source names. `processing/records.py` maps a raw scraper row through the cleaning functions.

## 10. Scraping approach

`BaseScraper` owns HTTP details:

- a `requests.Session()`
- a descriptive User-Agent
- a 15 second timeout
- retries with exponential backoff for HTTP 429, 500, 502, 503, 504 and network errors
- about **0.5 seconds between requests**
- logging of each page URL and failures

`BooksScraper` and `QuotesScraper` only parse HTML. Individual cards are parsed in a try/except so one bad record does not stop the page.

Books start at `https://books.toscrape.com/`. Each card is `article.product_pod`. The title comes from `h3 > a[title]` because the visible text is truncated. Price is `p.price_color`. Rating is a class on `p.star-rating` (`One`–`Five`). The product URL is joined with `urllib.parse.urljoin`.

Quotes start at `https://quotes.toscrape.com/`. Each card is `div.quote`. Text is `span.text`, author is `small.author`, tags are `a.tag`. `source_url` is the **listing page URL** where the quote was found, because quotes do not have a unique permalink on that site.

A failure while scraping books does not skip quotes, and the reverse is also true. Each source is wrapped in its own try/except in `main.py`.

## 11. Pagination approach

Pagination never uses a hard-coded page range.

1. Request the start URL.
2. Parse records.
3. Look for `li.next > a`.
4. If it exists, `urljoin` the `href` onto the current page URL and continue.
5. Stop when that link is missing.

If the sites add or remove pages, the scraper follows whatever “next” links exist.

## 12. Data model

CSV columns are always written in this order:

| Field | Books | Quotes |
| --- | --- | --- |
| `source` | `Books to Scrape` | `Quotes to Scrape` |
| `source_url` | product URL | listing page URL |
| `name_or_title` | book title | quote text (quotes stripped) |
| `category` | empty | empty |
| `price` | float, e.g. `51.77` | empty |
| `rating` | integer 1–5 | empty |
| `author` | empty | author name |
| `tags` | empty | lowercase tags joined by `;` |
| `description` | empty | empty |
| `scraped_at` | UTC ISO timestamp | UTC ISO timestamp |

Empty inapplicable fields are written as blank CSV cells, not invented values.

### Book category and description

Listing pages do not contain category or product description. This project **does not fetch book detail pages**.

Reason: there are 1000 books. One extra request per book at 0.5 seconds would add about 8 minutes and still be optional data. The assignment allows those fields to stay empty when they are not obtained. The pipeline never guesses them.

## 13. Cleaning approach

`processing/cleaning.py` contains pure functions used after scraping:

- `clean_text` — None-safe, replaces non-breaking spaces, collapses whitespace
- `strip_quotes` — removes wrapping `"`, `'`, `“”`, `‘’`
- `clean_price` — turns `£51.77` / `$1,234.50` into floats; returns None if no number
- `clean_rating` — `One`–`Five` (and class strings like `star-rating Three`) to 1–5
- `clean_tags` — trim, lowercase, unique, sort, join with `;`
- `normalize_url` — produce an absolute `http://` or `https://` URL

## 14. Validation approach

`validate_record(record) -> list[str]` returns an empty list when the row is valid.

Reason codes include:

- `unknown_source`
- `missing_name`
- `invalid_url`
- `invalid_price`
- `invalid_rating`

Invalid rows are counted, logged at WARNING, excluded from the CSV, and summarized in JSON. Validation does not raise.

## 15. Duplicate detection approach

Identifying fields are normalized by lowercasing, removing punctuation, and collapsing whitespace. A SHA-256 hex digest is then computed.

Keys:

- **Books:** `source + title`
- **Quotes:** `source + author + first 50 characters of the normalized quote`

The first record with a fingerprint is kept. Later matches are counted as duplicates and omitted from the CSV.

On a live run, books had **one** duplicate: the title `The Star-Touched Queen` appears twice on Books to Scrape as two product URLs. The assignment rule uses title, not URL, so the second copy is dropped and counted.

Unit tests prove that `"Example Book Title"`, `" Example Book Title "`, and `"EXAMPLE BOOK TITLE"` hash to the same fingerprint.

## 16. Error handling

- HTTP retries for temporary status codes and `requests` exceptions
- missing HTML elements are treated as absent fields or skipped records
- one malformed card does not stop a page
- one failed source does not stop the other source
- unexpected exceptions are logged with stack traces

## 17. Logging

Logging goes to the console and `logs/scraper.log` with UTC timestamps.

- INFO: start, each page request, successful page processing, source completion, final statistics
- WARNING: rejected records, missing optional elements, recoverable parse issues, duplicates
- ERROR: failed HTTP requests, unrecoverable source failures

## 18. Output files

Verified live run (2026-10-06):

| Metric | Value |
| --- | --- |
| Books pages | 50 ok, 0 failed |
| Quotes pages | 10 ok, 0 failed |
| Raw records | 1000 books + 100 quotes = 1100 |
| Rejected | 0 |
| Duplicates | 1 book (`The Star-Touched Queen`) |
| Final CSV rows | **1099** (999 books + 100 quotes) |
| Duration | ~62 seconds |

`summary_report.json` `final_record_count` matches the CSV row count.

Prices in the CSV are numeric. Book ratings are integers 1–5.

## 19. Testing

```bash
python -m pytest -q
```

Coverage:

- cleaning: whitespace, nbsp, price, rating, tags, URLs
- validation: valid row plus missing name, bad URL, bad price, bad rating, unknown source
- deduplication: exact, case, whitespace, punctuation, distinct rows stay unique
- scraper parsing: local HTML fixtures, including `li.next` handling

No test requires live network access.

## 20. Assumptions

- The two sites remain publicly available without authentication.
- Quote `source_url` is the page the quote was scraped from.
- Book category/description stay empty unless listing HTML contains them (it does not).
- Duplicate books with the same normalized title are intentionally collapsed.

## 21. Known limitations

- Category and description are empty for books because detail pages are not fetched.
- Quotes share a page-level URL, not a per-quote permalink.
- Duplicate detection can collapse two different products that share a title (observed: `The Star-Touched Queen`).
- If a listing page fails after retries, pagination for that source stops because the next URL cannot be discovered.
- Request delay is polite but not adaptive beyond 429 retries.
- Local verification used Python 3.9; the assignment asks for 3.10–3.12. Prefer 3.10+ when submitting if the company environment requires it.

## 22. AI usage summary

Cursor (Grok 4.6) was used to implement the pipeline from the assignment text, write tests, run pytest, run `python main.py`, and draft documentation. See `AI_USAGE.md` for a full account. Review the code yourself before an interview; you need to be able to explain every file.
