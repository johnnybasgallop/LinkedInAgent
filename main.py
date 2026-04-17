"""
main.py — Pipeline orchestrator

Stage 1 — Scrape job cards from LinkedIn search
Stage 2 — Fetch full descriptions for each job
Stage 3 — Filter jobs against resume variants via Claude
Stage 4 — Send notifications for matched jobs (WhatsApp or Telegram)
"""

import asyncio
import json
from datetime import datetime, timedelta

from config import OUTPUT_FILE
from browser.context import create_context, teardown
from pipeline.cache import filter_uncached, load_cache, save_cache, update_cache
from pipeline.cards import scrape_job_cards
from pipeline.descriptions import fetch_all_descriptions
from pipeline.filter import filter_jobs
from pipeline.messaging import send_messages
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

        # Split early so Stage 2 skips jobs already in cache
        cache = load_cache()
        uncached_jobs, cached_hits = filter_uncached(jobs, cache)
        print(f"[Cache] {len(cached_hits)} job(s) already analysed, {len(uncached_jobs)} new/expired.")

        # Stage 2 — fetch descriptions (only for uncached jobs)
        uncached_jobs = await fetch_all_descriptions(page, uncached_jobs)

    finally:
        await teardown(playwright, browser)

    # Stage 3 — LLM filter (cache-aware)
    if uncached_jobs:
        all_scored = filter_jobs(uncached_jobs, resumes)
        update_cache(cache, all_scored)
        save_cache(cache)

    # Pull all results (new + cached), filter by score threshold for output only
    _MIN_SCORE = 6
    _RENOTIFY_AFTER_HOURS = 24
    all_results = [cache[job["id"]] for job in jobs if job["id"] in cache]
    matched_jobs = sorted(
        [j for j in all_results if j["score"] >= _MIN_SCORE],
        key=lambda x: x["score"], reverse=True
    )

    # Split: send new jobs + reposts (not notified in last 24h); suppress the rest.
    cutoff = datetime.now() - timedelta(hours=_RENOTIFY_AFTER_HOURS)
    to_send, suppressed = [], []
    for j in matched_jobs:
        notified_at = j.get("notified_at")
        if notified_at:
            try:
                if datetime.fromisoformat(notified_at) >= cutoff:
                    suppressed.append(j)
                    continue
            except ValueError:
                pass  # malformed timestamp — fall through and resend
        to_send.append(j)

    if suppressed:
        print(f"[Notify] suppressed {len(suppressed)} matched job(s) notified within last {_RENOTIFY_AFTER_HOURS}h:")
        for j in suppressed:
            print(f"  [{j['score']}/10] {j['title']} @ {j['company']} — last notified {j.get('notified_at')}")

    # Stage 4 — notify matched jobs (platform chosen in config)
    send_messages(to_send)

    # Stamp notified_at on jobs we just sent, persist cache
    if to_send:
        now_iso = datetime.now().isoformat(timespec="seconds")
        for j in to_send:
            cache[j["id"]]["notified_at"] = now_iso
        save_cache(cache)

    # Persist matched results (full list, including suppressed)
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(matched_jobs, indent=2, ensure_ascii=False))

    print(f"\n[Done] {len(matched_jobs)}/{len(jobs)} jobs matched, {len(to_send)} sent. Saved to {OUTPUT_FILE}")
    for job in matched_jobs:
        print(f"  [{job['score']}/10] {job['title']} @ {job['company']} — {job['reason']}")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
