"""
main.py — Pipeline orchestrator
Runs all stages in sequence:
  1. Scrape job cards from LinkedIn search
  2. Fetch full descriptions for each job
  3. (Soon) Send WhatsApp notifications for new jobs
  4. Save results to data/jobs.json
"""

import asyncio
import json

from config import OUTPUT_FILE
from browser.context import create_context, teardown
from pipeline.cards import scrape_job_cards
from pipeline.descriptions import fetch_all_descriptions


async def run_pipeline() -> None:
    playwright, browser, context = await create_context()
    page = await context.new_page()

    try:
        # Stage 1 — cards
        jobs = await scrape_job_cards(page)
        if not jobs:
            print("No jobs found. Exiting.")
            return

        # Stage 2 — descriptions
        jobs = await fetch_all_descriptions(page, jobs)

        # Stage 3 — notify (coming soon)
        # notify_jobs(new_jobs)

    finally:
        await teardown(playwright, browser)

    # Persist results
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(jobs, indent=2, ensure_ascii=False))
    print(f"\n[Done] {len(jobs)} jobs saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
