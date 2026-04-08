"""
Stage 3 — Notify
Sends job alerts via WhatsApp using the CallMeBot API.
(Stub — to be wired up with credentials from .env)
"""

import os


def _format_message(job: dict) -> str:
    desc_preview = job.get("description", "")[:300]
    if len(job.get("description", "")) > 300:
        desc_preview += "..."

    return (
        f"*{job['title']}* @ {job['company']}\n"
        f"{job['location']} | {job['posted']}\n"
        f"{job['url']}\n\n"
        f"{desc_preview}"
    )


def send_whatsapp(job: dict) -> bool:
    """
    Send a WhatsApp message for a single job via CallMeBot.
    Returns True on success, False on failure.
    Requires CALLMEBOT_PHONE and CALLMEBOT_APIKEY in environment / .env
    """
    # TODO: wire up once credentials are configured
    raise NotImplementedError("notify.py not yet configured — set up .env first.")


def notify_jobs(jobs: list[dict]) -> None:
    """Send WhatsApp alerts for a list of new jobs."""
    print(f"\n[Stage 3] Sending {len(jobs)} WhatsApp notifications...")
    for job in jobs:
        try:
            send_whatsapp(job)
            print(f"  Sent: {job['title']} @ {job['company']}")
        except Exception as e:
            print(f"  Failed to send for {job['title']}: {e}")
