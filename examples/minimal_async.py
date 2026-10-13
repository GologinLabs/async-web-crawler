"""The smallest async Playwright crawler: one queue, a seen set, 16 tabs."""
import asyncio

from playwright.async_api import async_playwright

START, LIMIT, TABS = "https://books.toscrape.com/", 100, 16
LINKS = (f"els => els.map(e => e.href.split('#')[0])"
         f".filter(h => h.startsWith('{START}'))")  # same-site links only


async def worker(page, queue, seen):
    while True:
        url = await queue.get()
        try:
            await page.goto(url)
            for link in await page.eval_on_selector_all("a[href]", LINKS):
                if link not in seen and len(seen) < LIMIT:
                    seen.add(link)  # dedupe before enqueueing
                    queue.put_nowait(link)
        except Exception:
            pass  # one bad page must not stop the worker
        finally:
            queue.task_done()


async def main():
    queue, seen = asyncio.Queue(), {START}
    queue.put_nowait(START)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        tabs = [await browser.new_page() for _ in range(TABS)]
        workers = [asyncio.create_task(worker(t, queue, seen)) for t in tabs]
        await queue.join()  # every queued URL was handled
        for w in workers:
            w.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
    print(len(seen), "pages")

asyncio.run(main())
