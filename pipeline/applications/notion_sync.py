"""
Push a matched job into the Notion applications database.
Called when the user taps "Applied" on a Telegram notification.
"""

from datetime import date

from notion_client import Client

from config import NOTION_DATABASE_ID, NOTION_TOKEN

_DATA_SOURCE_ID: str | None = None


def _resolve_data_source_id(notion: Client) -> str | None:
    global _DATA_SOURCE_ID
    if _DATA_SOURCE_ID:
        return _DATA_SOURCE_ID
    try:
        db = notion.databases.retrieve(database_id=NOTION_DATABASE_ID)
        sources = db.get("data_sources") or []
        if sources:
            _DATA_SOURCE_ID = sources[0].get("id")
            return _DATA_SOURCE_ID
    except Exception as e:
        print(f"[Notion] failed to resolve data source id: {e}")
    return None


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


def fetch_applied_urls() -> set[str]:
    """Return all JobUrl values currently in the Notion applications DB."""
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        return set()

    notion = Client(auth=NOTION_TOKEN)
    data_source_id = _resolve_data_source_id(notion)
    if not data_source_id:
        return set()

    urls: set[str] = set()
    start_cursor: str | None = None
    try:
        while True:
            kwargs = {"data_source_id": data_source_id, "page_size": 100}
            if start_cursor:
                kwargs["start_cursor"] = start_cursor
            result = notion.data_sources.query(**kwargs)
            for page in result.get("results", []):
                prop = (page.get("properties") or {}).get("JobUrl") or {}
                url = prop.get("url")
                if url:
                    urls.add(url)
            if not result.get("has_more"):
                break
            start_cursor = result.get("next_cursor")
    except Exception as e:
        print(f"[Notion] failed to fetch applied URLs: {e}")
    return urls


def _application_exists(notion: Client, url: str) -> bool:
    if not url:
        return False
    data_source_id = _resolve_data_source_id(notion)
    if not data_source_id:
        return False
    try:
        result = notion.data_sources.query(
            data_source_id=data_source_id,
            filter={"property": "JobUrl", "url": {"equals": url}},
            page_size=1,
        )
        return bool(result.get("results"))
    except Exception as e:
        print(f"[Notion] duplicate check failed, proceeding with insert: {e}")
        return False


def create_application(job: dict) -> str:
    """Returns 'created', 'duplicate', 'skipped', or 'failed'."""
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        print("[Notion] NOTION_TOKEN or NOTION_DATABASE_ID not set — skipping.")
        return "skipped"

    notion = Client(auth=NOTION_TOKEN)
    url = job.get("url") or None

    if _application_exists(notion, url):
        print(f"[Notion] duplicate: '{job.get('title')} @ {job.get('company')}' already tracked.")
        return "duplicate"

    properties = {
        "Company":      {"title":     _text(job.get("company", ""))},
        "Role":         {"rich_text": _text(job.get("title", ""))},
        "Score":        {"number":    job.get("score")},
        "Resume":       {"rich_text": _text(job.get("best_resume", ""))},
        "Location":     {"select":    {"name": _infer_location_kind(job.get("location", ""))}},
        "Date applied": {"date":      {"start": date.today().isoformat()}},
        "Notes":        {"rich_text": _text(job.get("reason", ""))},
        "JobUrl":       {"url":       url},
    }

    try:
        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties=properties,
        )
        print(f"[Notion] added '{job.get('title')} @ {job.get('company')}'")
        return "created"
    except Exception as e:
        print(f"[Notion] failed to add application: {e}")
        return "failed"
