"""The same crawl with Playwright's sync API: one tab, one page at a time."""
import sys
from collections import deque

from playwright.sync_api import sync_playwright

START, LIMIT = "https://books.toscrape.com/", 100
LINKS = (f"els => els.map(e => e.href.split('#')[0])"
         f".filter(h => h.startsWith('{START}'))")  # same-site links only


def main() -> None:
    queue, seen = deque([START]), {START}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        while queue:
            url = queue.popleft()
            try:
                page.goto(url)  # the whole program waits here
                for link in page.eval_on_selector_all("a[href]", LINKS):
                    if link not in seen and len(seen) < LIMIT:
                        seen.add(link)
                        queue.append(link)
            except Exception as exc:
                print("failed:", url, exc, file=sys.stderr)
        browser.close()
    print(len(seen), "pages")


main()
