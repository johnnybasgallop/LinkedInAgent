"""
filter_only.py
Runs Stage 3 (LLM filter) against an existing data/jobs.json.
Useful for testing without re-running the scraper.
"""

import json
from config import OUTPUT_FILE
from pipeline.filter import filter_jobs
from pipeline.resume import load_resumes


def main() -> None:
    if not OUTPUT_FILE.exists():
        print(f"No jobs file found at {OUTPUT_FILE} — run main.py first.")
        return

    jobs = json.loads(OUTPUT_FILE.read_text())
    print(f"Loaded {len(jobs)} jobs from {OUTPUT_FILE}")

    resumes = load_resumes()
    matched = filter_jobs(jobs, resumes)

    print(f"\n[Done] {len(matched)}/{len(jobs)} jobs matched.\n")
    for job in matched:
        print(f"  [{job['score']}/10] {job['title']} @ {job['company']}")
        print(f"    Resume: {job['best_resume']}")
        print(f"    Reason: {job['reason']}")
        print(f"    {job['url']}")
        print()


if __name__ == "__main__":
    main()
