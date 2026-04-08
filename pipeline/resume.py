"""
Resume Parser
Reads all .docx files from the resumes/ directory and returns
their plain text content keyed by filename stem.
"""

from pathlib import Path
from docx import Document

from config import RESUMES_DIR


def extract_text(path: Path) -> str:
    """Extract plain text from a .docx file."""
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def load_resumes() -> dict[str, str]:
    """
    Load all .docx files from the resumes directory.
    Returns a dict of { filename_stem: plain_text }.
    e.g. { "JB_SWE_FS": "...", "RESUME_BE": "..." }
    """
    if not RESUMES_DIR.exists():
        raise FileNotFoundError(f"Resumes directory not found: {RESUMES_DIR}")

    resumes = {}
    for path in sorted(RESUMES_DIR.glob("*.docx")):
        resumes[path.stem] = extract_text(path)

    if not resumes:
        raise FileNotFoundError(f"No .docx files found in {RESUMES_DIR}")

    print(f"[Resumes] Loaded {len(resumes)}: {', '.join(resumes.keys())}")
    return resumes
