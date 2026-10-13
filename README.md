# Async Web Crawler

An asynchronous Python web crawler. It fetches pages over HTTP first and uses
a browser only for the pages that need one, either local Chromium or
[Gologin Cloud Browser](https://gologin.com/cloud-browser/) profiles.

- Schedules requests per host, so a slow site doesn't hold up the others.
- Respects `robots.txt`, `Crawl-delay`, and `Retry-After`.
- Reads sitemaps and JSON-LD structured data before falling back to CSS
  selectors.
- Recrawls only the pages that changed.
- Can add each page's main content as markdown for LLM pipelines.

## Quickstart

Requires [uv](https://docs.astral.sh/uv/), which installs Python 3.13 or newer
for you.

```bash
git clone https://github.com/triposat/async-web-crawler
cd async-web-crawler
uv sync
uv run playwright install --with-deps chromium
uv run python crawler.py --backend http --max-pages 200 --interval 0
```

This crawls [books.toscrape.com](https://books.toscrape.com/), a sandbox built
for crawling practice, which is why it can skip the delay between requests.
Records go to `books.jsonl`, one JSON object per line:

```json
{"url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html", "title": "A Light in the Attic", "price": "\u00a351.77", "availability": "In stock (22 available)", "upc": "a897fe39b1053632", "content_signal": []}
```

When the crawl ends, a summary line prints how many pages were fetched and
how many records were stored.

## Crawl your own site

Set a User-Agent that links to a page saying who runs the crawler, and keep
at least 1 second between requests to a site you don't own:

```bash
uv run python crawler.py --backend http --per-host 1 --interval 1 \
  --seed https://example.com/ --include '/blog/' --pages --out pages.jsonl \
  --user-agent "MyCrawler/1.0 (+https://example.com/about-my-crawler)"
```

- `--include` limits the crawl to URLs that match a regex.
- Records come from JSON-LD articles and products. `--pages` adds a basic
  record (URL, title, `h1`, description) for every other page.
- `--markdown` adds each page's main content as markdown.
- `--sitemap --max-depth 0` reads the site's sitemaps instead of following
  links, and `--state state.json` makes the next run fetch only what changed.

To extract other fields, add CSS selectors for your site in `parse()` in
`crawler.py`. `uv run python crawler.py --help` lists every flag.

## Pages that need a browser

With `--escalate local`, the crawler fetches over HTTP and retries a page in
local Chromium when it's blocked or its HTML is empty until JavaScript runs:

```bash
uv run python crawler.py --backend http --escalate local --tabs 2 \
  --seed https://quotes.toscrape.com/js/ --include '/js/' --out quotes.jsonl
```

To render every page in a browser, use `--backend local` instead.

## Gologin Cloud Browser

The `gologin` backend runs the browser tabs in Gologin Cloud Browser profiles,
so Chromium doesn't use your machine's memory, and each profile keeps its
fingerprint, cookies, and storage between runs. Get an API token from the
Gologin dashboard under **API & MCP** > **API**, then create a profile once and
reuse it:

```bash
export GL_API_TOKEN="your-token"
uv run python gologin_pool.py 1 > profiles.txt   # creates 1 profile
uv run python crawler.py --backend gologin --profiles "$(cat profiles.txt)" \
  --tabs 16 --per-host 16 --interval 0
```

Each profile runs as 1 cloud session. To crawl faster on a plan with more
parallel sessions, create more profiles (for example `gologin_pool.py 3`) and
set `--per-host` to the number of profiles times `--tabs`. When the crawl
ends, or stops on an error or Ctrl+C, the crawler stops every cloud session it
opened.

To use the cloud only for pages that HTTP can't read, combine both:

```bash
uv run python crawler.py --backend http --escalate gologin \
  --profiles "$(cut -d, -f1 profiles.txt)" --tabs 2 \
  --seed https://quotes.toscrape.com/js/ --include '/js/' --out quotes.jsonl
```

`consistency.py` checks whether a browser's signals agree with each other, for
example after changing the User-Agent:

```bash
uv run python consistency.py gologin "$(cut -d, -f1 profiles.txt)"
uv run python consistency.py local-override
```

## Project layout

| Path | What it is |
|---|---|
| `crawler.py` | The crawler: frontier, `robots.txt`, sitemaps, parsing, HTTP and local fetchers |
| `gologin_pool.py` | The Gologin Cloud Browser fetcher, and a helper that creates profiles |
| `consistency.py` | Checks a browser for contradicting signals |
| `examples/` | A minimal async crawler and its synchronous version, for comparison |
| `benchmarks/` | Per-host frontier vs one shared queue, and sync vs async speed |
| `tests/` | Offline tests that need no network, browser, or token |

## Tests

```bash
uv run pytest -q
```

## License

MIT. See [LICENSE](LICENSE).
