"""
Resume Parser
Reads all .pdf files from the resumes/ directory and returns
their plain text content keyed by filename stem.
"""

from pathlib import Path

import pdfplumber

from config import RESUMES_DIR


def extract_text(path: Path) -> str:
    """Extract plain text from a .pdf file."""
    with pdfplumber.open(str(path)) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return "\n".join(pages).strip()


def load_resumes() -> dict[str, str]:
    """
    Load all .pdf files from the resumes directory.
    Returns a dict of { filename_stem: plain_text }.
    e.g. { "JB_FS_JS": "...", "JB_BE": "..." }
    """
    if not RESUMES_DIR.exists():
        raise FileNotFoundError(f"Resumes directory not found: {RESUMES_DIR}")

    resumes = {}
    for path in sorted(RESUMES_DIR.glob("*.pdf")):
        resumes[path.stem] = extract_text(path)

    if not resumes:
        raise FileNotFoundError(f"No .pdf files found in {RESUMES_DIR}")

    print(f"[Resumes] Loaded {len(resumes)}: {', '.join(resumes.keys())}")
    return resumes
