"""
Stage 1 — Job Cards
Scrapes the first page of LinkedIn job search results.
Returns a list of jobs with: id, title, company, location, posted, url.
"""

import asyncio
import random
from playwright.async_api import Page

from config import SEARCH_URL


async def _random_delay(min_s: float = 1.5, max_s: float = 3.5) -> None:
    await asyncio.sleep(random.uniform(min_s, max_s))


def _is_logged_in(url: str) -> bool:
    return "login" not in url and "authwall" not in url


async def scrape_job_cards(page: Page) -> list[dict]:
    """
    Navigate to the configured search URL and scrape all job cards
    on the first page. Returns a list of job dicts.
    """
    print("[Stage 1] Navigating to LinkedIn job search...")
    await page.goto(SEARCH_URL, wait_until="domcontentloaded")
    await _random_delay(2, 4)

    if not _is_logged_in(page.url):
        print("[Stage 1] ERROR: Session expired — re-run login.py.")
        return []

    try:
        await page.wait_for_selector("li[data-occludable-job-id]", timeout=15000)
    except Exception:
        print("[Stage 1] ERROR: No job cards found. LinkedIn layout may have changed.")
        return []

    cards = await page.query_selector_all("li[data-occludable-job-id]")
    print(f"[Stage 1] Found {len(cards)} cards. Scrolling to trigger lazy load...")

    for card in cards:
        await card.scroll_into_view_if_needed()
        await asyncio.sleep(0.15)
    await _random_delay(1, 2)

    jobs = []
    for card in cards:
        job = await _parse_card(card)
        if job:
            jobs.append(job)

    print(f"[Stage 1] Done — {len(jobs)} jobs scraped.")
    return jobs


async def _parse_card(card) -> dict | None:
    """Extract fields from a single job card element."""
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

        return {
            "id":       job_id,
            "title":    title,
            "company":  company,
            "location": location,
            "posted":   posted,
            "url":      f"https://www.linkedin.com/jobs/view/{job_id}/",
        }
    except Exception as e:
        print(f"  [Stage 1] Skipped card: {e}")
        return None
