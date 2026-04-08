from pathlib import Path

# Paths
ROOT_DIR       = Path(__file__).parent
SESSION_STATE  = ROOT_DIR / "session" / "state.json"
OUTPUT_FILE    = ROOT_DIR / "data" / "jobs.json"
SEEN_JOBS_FILE = ROOT_DIR / "data" / "seen_jobs.json"

# Browser
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# LinkedIn search URL
# Build your search on LinkedIn (keywords, location, filters), copy the URL, paste here.
SEARCH_URL = (
    "https://www.linkedin.com/jobs/search/"
    "?keywords=%22Software%20Engineer%22%20OR%20%22Fullstack%20Developer%22"
    "&location=United%20States"
    "&f_WT=2"     # remote only
    "&sortBy=DD"  # most recent
)
