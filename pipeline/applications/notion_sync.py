"""
Push a matched job into the Notion applications database.
Called when the user taps "Applied" on a Telegram notification.
"""

from datetime import date

from notion_client import Client

from config import NOTION_DATABASE_ID, NOTION_TOKEN


def _infer_location_kind(loc: str) -> str:
    lower = (loc or "").lower()
    if "remote" in lower:
        return "Remote"
    if "hybrid" in lower:
        return "Hybrid"
    return "On-Site"


def _text(content: str) -> list[dict]:
    if not content:
        return []
    return [{"type": "text", "text": {"content": content}}]


def create_application(job: dict) -> bool:
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        print("[Notion] NOTION_TOKEN or NOTION_DATABASE_ID not set — skipping.")
        return False

    notion = Client(auth=NOTION_TOKEN)

    properties = {
        "Company":      {"title":     _text(job.get("company", ""))},
        "Role":         {"rich_text": _text(job.get("title", ""))},
        "Score":        {"number":    job.get("score")},
        "Resume":       {"rich_text": _text(job.get("best_resume", ""))},
        "Location":     {"select":    {"name": _infer_location_kind(job.get("location", ""))}},
        "Date applied": {"date":      {"start": date.today().isoformat()}},
        "Notes":        {"rich_text": _text(job.get("reason", ""))},
        "JobUrl":       {"url":       job.get("url") or None},
    }

    try:
        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties=properties,
        )
        print(f"[Notion] added '{job.get('title')} @ {job.get('company')}'")
        return True
    except Exception as e:
        print(f"[Notion] failed to add application: {e}")
        return False
