import os
from datetime import time
from pathlib import Path
from urllib.parse import quote, urlencode

from dotenv import load_dotenv

load_dotenv()

# Scheduler — pipeline runs every N minutes between START and END (Europe/London)
SCRAPE_START            = time.fromisoformat(os.getenv("SCRAPE_START", "02:20"))
SCRAPE_END              = time.fromisoformat(os.getenv("SCRAPE_END",   "23:00"))
SCRAPE_INTERVAL_MINUTES = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "5"))

# Messaging — where matched jobs get delivered
MESSAGING_PLATFORM = os.getenv("MESSAGING_PLATFORM", "telegram")  # "telegram" | "whatsapp"
WHATSAPP_PHONE     = os.getenv("WHATSAPP_PHONE", "+447592515298")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

# Notion — applications tracking DB
NOTION_TOKEN       = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# Paths. STATE_DIR defaults to the repo root (local dev); on Railway set it
# to the mount path of the persistent volume (e.g. /app/state).
ROOT_DIR       = Path(__file__).parent
STATE_DIR      = Path(os.getenv("STATE_DIR", ROOT_DIR))
SESSION_STATE  = STATE_DIR / "session" / "state.json"
OUTPUT_FILE    = STATE_DIR / "data" / "jobs.json"
SEEN_JOBS_FILE = STATE_DIR / "data" / "seen_jobs.json"
CACHE_FILE     = STATE_DIR / "data" / "cache.json"
CACHE_TTL_DAYS = 30
RESUMES_DIR    = ROOT_DIR / "pipeline" / "resumes"

# Browser
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# LinkedIn search — boolean query is built from KEYWORDS (OR'd) and EXCLUDE_KEYWORDS
# (NOT'd). Everything is wrapped in quotes so LinkedIn treats each term literally.

KEYWORDS = [
    "backend developer",
    "fullstack",
    "full-stack",
    "backend engineer",
    "software engineer",
    "backend software developer",
    "fullstack engineer",
    "fullstack software engineer",
    "fullstack developer",
    "fullstack software developer",
    "python",
    "fastapi",
    "django",
    "software developer",
    "SWE",
]

EXCLUDE_KEYWORDS = [
    "lead",
    "principal",
    "intern",
    "graduate",
    "graduates",
    "new grad",
    "new graduate",
    "post grad",
    "postgraduate",
    "campus",
    "university",
    "Staff",
    "c++",
    "rust",
    "php",
    "ruby",
    "tutor",
    ".net",
    "senior",
]

# Shared across all searches — quality filters applied to every query.
BASE_SEARCH_PARAMS = {
    "f_VJ":    "true",  # verified employer
    "f_JT":    "F",     # full-time only
    "sortBy":  "DD",    # most recent first
}

# Each search is a scope: where and what work-type. Keywords/excludes are shared.
# f_WT codes: 1 = onsite, 2 = remote, 3 = hybrid.
SEARCHES = [
    {
        "name":     "remote_us",
        "location": "United States",
        "params":   {"f_WT": "2"},
    },
    {
        "name":     "onsite_hybrid_la",
        "location": "Los Angeles, California",
        "params":   {"f_WT": "1,3", "distance": "50"},
    },
]


def _build_boolean_query(keywords: list[str], exclude: list[str]) -> str:
    pos = " OR ".join(f'"{k}"' for k in keywords)
    neg = " ".join(f'NOT "{k}"' for k in exclude)
    return f"({pos}) {neg}".strip() if neg else f"({pos})"


def _build_search_url(search: dict) -> str:
    params = {
        "keywords": _build_boolean_query(KEYWORDS, EXCLUDE_KEYWORDS),
        "location": search["location"],
        **BASE_SEARCH_PARAMS,
        **search["params"],
    }
    return "https://www.linkedin.com/jobs/search/?" + urlencode(params, quote_via=quote)


# List of (name, url) tuples — consumed by the scraper stage.
SEARCH_URLS = [(s["name"], _build_search_url(s)) for s in SEARCHES]
