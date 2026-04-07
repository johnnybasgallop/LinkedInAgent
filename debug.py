"""Quick debug script — screenshots the page and dumps the HTML so we can find the right selectors."""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

SESSION_STATE = "./session/state.json"
SEARCH_URL = (
    "https://www.linkedin.com/jobs/search/"
    "?keywords=%22Software%20Engineer%22%20OR%20%22Fullstack%20Developer%22"
    "&location=United%20States"
    "&f_WT=2"
    "&sortBy=DD"
)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # visible so we can see what's happening
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            storage_state="./session/state.json",
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )

        page = await context.new_page()
        await page.goto(SEARCH_URL, wait_until="domcontentloaded")
        await asyncio.sleep(5)  # let JS render fully

        # Screenshot
        await page.screenshot(path="debug_screenshot.png", full_page=False)
        print("Screenshot saved to debug_screenshot.png")

        # Dump a portion of the HTML
        html = await page.content()
        Path("debug_page.html").write_text(html)
        print(f"Full HTML saved to debug_page.html ({len(html)} chars)")

        # Print current URL (check if we got redirected)
        print(f"Current URL: {page.url}")

        # Try some common job card selectors and report which exist
        selectors = [
            "li[data-occludable-job-id]",
            "div[data-job-id]",
            ".job-card-container",
            ".jobs-search-results__list-item",
            ".scaffold-layout__list-container li",
            "ul.jobs-search__results-list li",
            "[class*='job-card']",
            "[data-entity-urn]",
        ]

        print("\n--- Selector hits ---")
        for sel in selectors:
            els = await page.query_selector_all(sel)
            print(f"  {sel!r:55s} → {len(els)} elements")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
