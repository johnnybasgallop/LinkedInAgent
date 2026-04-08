"""
LinkedIn Job Scraper
====================
Stage 1 — scrape_job_cards : pulls title, company, location, posted date, and URL
                              from the first page of the configured search results.
Stage 2 — fetch_description : navigates to each job URL and extracts the full
                              description text.

Output: jobs.json
"""

import asyncio
import json
import random
from pathlib import Path
from playwright.async_api import async_playwright, Page

SESSION_STATE = "./session/state.json"
OUTPUT_FILE   = "jobs.json"

SEARCH_URL = (
    "https://www.linkedin.com/jobs/search/"
    "?keywords=%22Software%20Engineer%22%20OR%20%22Fullstack%20Developer%22"
    "&location=United%20States"
    "&f_WT=2"       # remote only
    "&sortBy=DD"    # most recent
    "&f_TPR=r3600"  # posted in last hour — adjust as needed
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def random_delay(min_s: float = 1.5, max_s: float = 3.5) -> None:
    await asyncio.sleep(random.uniform(min_s, max_s))


def is_logged_in(url: str) -> bool:
    return "login" not in url and "authwall" not in url


def make_browser_context(playwright):
    return playwright.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"],
    )


# ---------------------------------------------------------------------------
# Stage 1 — Job cards
# ---------------------------------------------------------------------------

async def scrape_job_cards(page: Page) -> list[dict]:
    """
    Navigate to the search URL and return a list of job card dicts:
    id, title, company, location, posted, url.
    """
    print("[Stage 1] Navigating to search URL...")
    await page.goto(SEARCH_URL, wait_until="domcontentloaded")
    await random_delay(2, 4)

    if not is_logged_in(page.url):
        print("ERROR: Session expired — re-run login.py.")
        return []

    try:
        await page.wait_for_selector("li[data-occludable-job-id]", timeout=15000)
    except Exception:
        print("ERROR: No job cards found. LinkedIn may have changed its layout.")
        return []

    cards = await page.query_selector_all("li[data-occludable-job-id]")
    print(f"[Stage 1] Found {len(cards)} cards. Scrolling to load all...")

    for card in cards:
        await card.scroll_into_view_if_needed()
        await asyncio.sleep(0.15)
    await random_delay(1, 2)

    jobs = []
    for card in cards:
        try:
            job_id = await card.get_attribute("data-occludable-job-id")

            title_el = await card.query_selector(
                "a.job-card-list__title--link span[aria-hidden='true'] strong"
            )
            title = (await title_el.inner_text()).strip() if title_el else "N/A"

            company_el = await card.query_selector(".artdeco-entity-lockup__subtitle span")
            company = (await company_el.inner_text()).strip() if company_el else "N/A"

            location_el = await card.query_selector(
                ".job-card-container__metadata-wrapper li span"
            )
            location = (await location_el.inner_text()).strip() if location_el else "N/A"

            time_el = await card.query_selector("time")
            posted = (
                (await time_el.get_attribute("datetime") or await time_el.inner_text()).strip()
                if time_el else "N/A"
            )

            jobs.append({
                "id":       job_id,
                "title":    title,
                "company":  company,
                "location": location,
                "posted":   posted,
                "url":      f"https://www.linkedin.com/jobs/view/{job_id}/",
            })
        except Exception as e:
            print(f"  Skipped a card: {e}")

    print(f"[Stage 1] Scraped {len(jobs)} jobs.")
    return jobs


# ---------------------------------------------------------------------------
# Stage 2 — Descriptions
# ---------------------------------------------------------------------------

async def fetch_description(page: Page, job: dict) -> str:
    """
    Navigate to the job's URL and return the full description text.
    Returns an empty string if the description cannot be found.
    """
    try:
        await page.goto(job["url"], wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(3)

        # LinkedIn uses two different layouts; try both
        for selector in (
            '[data-testid="expandable-text-box"]',
            ".feed-shared-inline-show-more-text p",
        ):
            el = await page.query_selector(selector)
            if el:
                text = (await el.inner_text()).strip()
                text = text.replace("… more", "").replace("…more", "").strip()
                return text

    except Exception as e:
        print(f"  Could not fetch description for '{job['title']}': {e}")

    return ""


async def fetch_all_descriptions(page: Page, jobs: list[dict]) -> list[dict]:
    """
    Iterate through jobs, fetch each description, and attach it.
    Returns the enriched job list.
    """
    print(f"\n[Stage 2] Fetching descriptions for {len(jobs)} jobs...")
    for i, job in enumerate(jobs, 1):
        job["description"] = await fetch_description(page, job)
        status = f"{len(job['description'])} chars" if job["description"] else "FAILED"
        print(f"  [{i}/{len(jobs)}] {job['title']} @ {job['company']} — {status}")
        await random_delay(1, 2)

    return jobs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    if not Path(SESSION_STATE).exists():
        print("No session found — run login.py first.")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            storage_state=SESSION_STATE,
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        # Stage 1
        jobs = await scrape_job_cards(page)
        if not jobs:
            await browser.close()
            return

        # Stage 2
        jobs = await fetch_all_descriptions(page, jobs)
        await browser.close()

    # Output — keep only the fields we care about
    output = [
        {
            "id":          job["id"],
            "title":       job["title"],
            "company":     job["company"],
            "location":    job["location"],
            "posted":      job["posted"],
            "url":         job["url"],
            "description": job["description"],
        }
        for job in jobs
    ]

    Path(OUTPUT_FILE).write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n[Done] {len(output)} jobs saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
