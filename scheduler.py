"""
scheduler.py — Long-running scheduler for the scrape pipeline.

Runs run_pipeline() every SCRAPE_INTERVAL_MINUTES between SCRAPE_START and
SCRAPE_END in America/Los_Angeles. Designed as the entrypoint of a long-lived
worker (e.g. a Railway service).
"""

import asyncio
import time as time_mod
import traceback
from datetime import datetime, timedelta
from datetime import time as dtime
from zoneinfo import ZoneInfo

from config import SCRAPE_END, SCRAPE_INTERVAL_MINUTES, SCRAPE_START
from main import run_pipeline

TZ = ZoneInfo("America/Los_Angeles")


def _in_window(now: datetime, start: dtime, end: dtime) -> bool:
    t = now.time()
    if start <= end:
        return start <= t < end
    # window wraps past midnight (e.g. 13:30 → 02:00)
    return t >= start or t < end


def _seconds_until_window_opens(now: datetime, start: dtime) -> float:
    target = datetime.combine(now.date(), start, tzinfo=now.tzinfo)
    if now < target:
        return (target - now).total_seconds()
    tomorrow = datetime.combine(now.date() + timedelta(days=1), start, tzinfo=now.tzinfo)
    return (tomorrow - now).total_seconds()


def main() -> None:
    print(
        f"[Scheduler] starting · window {SCRAPE_START}–{SCRAPE_END} America/Los_Angeles · "
        f"every {SCRAPE_INTERVAL_MINUTES} min"
    )

    while True:
        now = datetime.now(TZ)

        if _in_window(now, SCRAPE_START, SCRAPE_END):
            next_tick = now + timedelta(minutes=SCRAPE_INTERVAL_MINUTES)
            print(f"[Scheduler] tick at {now:%Y-%m-%d %H:%M:%S %Z}")

            try:
                asyncio.run(run_pipeline())
            except Exception as e:
                print(f"[Scheduler] pipeline crashed: {e}")
                traceback.print_exc()

            now = datetime.now(TZ)
            sleep_s = max(0.0, (next_tick - now).total_seconds())
            if sleep_s > 0:
                print(f"[Scheduler] sleeping {sleep_s:.0f}s until next tick")
                time_mod.sleep(sleep_s)
        else:
            sleep_s = min(_seconds_until_window_opens(now, SCRAPE_START), 3600)
            print(f"[Scheduler] outside window ({now:%H:%M %Z}), sleeping {sleep_s:.0f}s")
            time_mod.sleep(sleep_s)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Scheduler] shutting down.")
