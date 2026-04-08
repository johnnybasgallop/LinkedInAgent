"""
Stage 2 — Descriptions
Navigates to each job's URL and extracts the full description text.
LinkedIn uses two different page layouts; both are handled.
"""

import asyncio
import random
from playwright.async_api import Page


async def _random_delay(min_s: float = 1.0, max_s: float = 2.5) -> None:
    await asyncio.sleep(random.uniform(min_s, max_s))


# Selectors in priority order — LinkedIn uses different layouts per job
_DESCRIPTION_SELECTORS = (
    '[data-testid="expandable-text-box"]',
    ".feed-shared-inline-show-more-text p",
)


async def fetch_description(page: Page, job: dict) -> str:
    """
    Navigate to a job URL and return the full description text.
    Returns an empty string if no description can be found.
    """
    try:
        await page.goto(job["url"], wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(3)

        for selector in _DESCRIPTION_SELECTORS:
            el = await page.query_selector(selector)
            if el:
                text = (await el.inner_text()).strip()
                text = text.replace("… more", "").replace("…more", "").strip()
                return text

    except Exception as e:
        print(f"  [Stage 2] Failed for '{job['title']}': {e}")

    return ""


async def fetch_all_descriptions(page: Page, jobs: list[dict]) -> list[dict]:
    """
    Enrich each job dict with a 'description' field.
    Returns the same list with descriptions attached.
    """
    print(f"\n[Stage 2] Fetching descriptions for {len(jobs)} jobs...")

    for i, job in enumerate(jobs, 1):
        job["description"] = await fetch_description(page, job)
        status = f"{len(job['description'])} chars" if job["description"] else "no description found"
        print(f"  [{i}/{len(jobs)}] {job['title']} @ {job['company']} — {status}")
        await _random_delay()

    print(f"[Stage 2] Done.")
    return jobs
