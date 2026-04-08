"""
main.py — Pipeline orchestrator

Stage 1 — Scrape job cards from LinkedIn search
Stage 2 — Fetch full descriptions for each job
Stage 3 — Filter jobs against resume variants via Claude
Stage 4 — (Soon) Send WhatsApp notifications for matched jobs
"""

import asyncio
import json

from config import OUTPUT_FILE
from browser.context import create_context, teardown
from pipeline.cards import scrape_job_cards
from pipeline.descriptions import fetch_all_descriptions
from pipeline.filter import filter_jobs
from pipeline.resume import load_resumes


async def run_pipeline() -> None:
    # Load resumes upfront — fail fast if missing
    resumes = load_resumes()

    playwright, browser, context = await create_context()
    page = await context.new_page()

    try:
        # Stage 1 — scrape job cards
        jobs = await scrape_job_cards(page)
        if not jobs:
            print("No jobs found. Exiting.")
            return

        # Stage 2 — fetch descriptions
        jobs = await fetch_all_descriptions(page, jobs)

    finally:
        await teardown(playwright, browser)

    # Stage 3 — LLM filter
    matched_jobs = filter_jobs(jobs, resumes)

    # Stage 4 — notify (coming soon)
    # notify_jobs(matched_jobs)

    # Persist matched results
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(matched_jobs, indent=2, ensure_ascii=False))

    print(f"\n[Done] {len(matched_jobs)}/{len(jobs)} jobs matched. Saved to {OUTPUT_FILE}")
    for job in matched_jobs:
        print(f"  [{job['score']}/10] {job['title']} @ {job['company']} — {job['reason']}")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
