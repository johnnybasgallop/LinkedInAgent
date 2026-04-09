"""
pipeline/cache.py — JSON-backed cache for Claude job analysis results.

Cache is keyed by LinkedIn job ID. Each entry stores the score, best_resume,
reason, and a cached_at timestamp. Entries older than CACHE_TTL_DAYS are treated
as expired and will be re-sent to Claude (handles reposted jobs).
"""

import json
from datetime import datetime, timedelta

from config import CACHE_FILE, CACHE_TTL_DAYS


def load_cache() -> dict:
    """Read cache from disk. Returns empty dict if file is missing or corrupt."""
    if not CACHE_FILE.exists():
        return {}
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        print("[Cache] Warning: cache file unreadable, starting fresh.")
        return {}


def save_cache(cache: dict) -> None:
    """Write cache dict to disk."""
    CACHE_FILE.parent.mkdir(exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def filter_uncached(jobs: list[dict], cache: dict) -> tuple[list[dict], list[dict]]:
    """
    Split jobs into two lists:
      - uncached: new jobs or TTL-expired entries that need Claude analysis
      - cached_hits: jobs with a still-valid cache entry (skip Claude)
    """
    cutoff = datetime.now() - timedelta(days=CACHE_TTL_DAYS)
    uncached, cached_hits = [], []

    for job in jobs:
        entry = cache.get(job["id"])
        if entry is None:
            uncached.append(job)
            continue
        try:
            entry_time = datetime.fromisoformat(entry["cached_at"])
        except (KeyError, ValueError):
            uncached.append(job)
            continue
        if entry_time > cutoff:
            cached_hits.append(job)
        else:
            uncached.append(job)

    return uncached, cached_hits


def update_cache(cache: dict, analysed_jobs: list[dict]) -> None:
    """
    Store full job data + Claude scores in the cache dict (in-place).
    Stores ALL scored jobs regardless of score so they are never re-sent to Claude.
    Call save_cache() afterwards to persist to disk.
    """
    now = datetime.now().isoformat(timespec="seconds")
    for job in analysed_jobs:
        cache[job["id"]] = {**job, "cached_at": now}
