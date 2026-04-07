"""
LinkedIn job scraper.
Loads a saved LinkedIn session and scrapes the first page of job results.
"""

import asyncio
import json
import random
from pathlib import Path
from playwright.async_api import async_playwright

SESSION_STATE = "./session/state.json"

# Edit this to your LinkedIn job search URL.
# Build it manually on LinkedIn (set keywords, location, remote, sort by most recent)
# then copy the URL here.
SEARCH_URL = (
    "https://www.linkedin.com/jobs/search/"
    "?keywords=%22Software%20Engineer%22%20OR%20%22Fullstack%20Developer%22"
    "&location=United%20States"
    "&f_WT=2"       # remote only
    "&sortBy=DD"    # most recent
    "&f_TPR=r3600"  # posted in last hour (change as needed)
)


async def random_delay(min_s=1.5, max_s=3.5):
    await asyncio.sleep(random.uniform(min_s, max_s))


async def check_logged_in(page) -> bool:
    """Returns False if LinkedIn has redirected us to the login page."""
    return "login" not in page.url and "authwall" not in page.url


async def scrape_jobs(page) -> list[dict]:
    """Scrape job cards from the first page of results."""
    print(f"Navigating to search URL...")
    await page.goto(SEARCH_URL, wait_until="domcontentloaded")
    await random_delay(2, 4)

    if not await check_logged_in(page):
        print("ERROR: Session expired. Re-run login.py to refresh your session.")
        return []

    # Wait for job cards to appear
    try:
        await page.wait_for_selector("li[data-occludable-job-id]", timeout=15000)
    except Exception:
        print("ERROR: Could not find job listings. LinkedIn may have changed its layout.")
        return []

    job_cards = await page.query_selector_all("li[data-occludable-job-id]")
    print(f"Found {len(job_cards)} job cards on first page.")

    # Scroll each card into view to trigger lazy loading of off-screen cards
    for card in job_cards:
        await card.scroll_into_view_if_needed()
        await asyncio.sleep(0.2)

    await random_delay(1, 2)

    jobs = []
    for card in job_cards:
        try:
            job_id = await card.get_attribute("data-occludable-job-id")

            # Use aria-hidden span > strong to avoid the duplicate visually-hidden text
            title_el = await card.query_selector("a.job-card-list__title--link span[aria-hidden='true'] strong")
            title = (await title_el.inner_text()).strip() if title_el else "N/A"

            company_el = await card.query_selector(".artdeco-entity-lockup__subtitle span")
            company = (await company_el.inner_text()).strip() if company_el else "N/A"

            # Location is inside the metadata-wrapper list
            location_el = await card.query_selector(".job-card-container__metadata-wrapper li span")
            location = (await location_el.inner_text()).strip() if location_el else "N/A"

            # Posted time lives in the footer
            time_el = await card.query_selector("time")
            posted = (await time_el.get_attribute("datetime") or await time_el.inner_text()).strip() if time_el else "N/A"

            job_url = f"https://www.linkedin.com/jobs/view/{job_id}/"

            jobs.append({
                "id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "posted": posted,
                "url": job_url,
            })
        except Exception as e:
            print(f"  Skipped a card due to error: {e}")
            continue

    return jobs


async def get_description(page, job: dict) -> str:
    """Navigate to a job page and return the full description text."""
    try:
        await page.goto(job["url"], wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(3)  # let JS render the description

        # LinkedIn uses two different layouts depending on the job
        for selector in (
            '[data-testid="expandable-text-box"]',
            ".feed-shared-inline-show-more-text p",
        ):
            desc_el = await page.query_selector(selector)
            if desc_el:
                text = (await desc_el.inner_text()).strip()
                text = text.replace("… more", "").replace("…more", "").strip()
                return text
    except Exception as e:
        print(f"  Could not fetch description for {job['title']}: {e}")

    return ""


async def main():
    if not Path(SESSION_STATE).exists():
        print("No session found. Run login.py first.")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
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
        jobs = await scrape_jobs(page)

        if not jobs:
            await browser.close()
            return

        print("\n--- Jobs Found ---\n")
        for job in jobs:
            print(f"[{job['posted']}] {job['title']} @ {job['company']}")
            print(f"  {job['location']}")
            print(f"  {job['url']}")
            print()

        # Fetch full description for first job as a test
        print("--- Full description for first job ---\n")
        job = jobs[0]
        desc = await get_description(page, job)
        print(f"{job['title']} @ {job['company']}")
        print(f"\n{desc}\n")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
