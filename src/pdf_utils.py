"""pdf_utils.py — turn a PDF into a list of (page_number, text)."""
from pathlib import Path

from pypdf import PdfReader


def read_pages(path: Path) -> list[tuple[int, str]]:
    reader = PdfReader(str(path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append((i, text))
    return pages


def pages_as_marked_text(pages: list[tuple[int, str]], max_chars: int = 60_000) -> str:
    """Join pages with clear markers so the LLM can tell us which page said what."""
    out = "\n\n".join(f"=== PAGE {n} ===\n{t}" for n, t in pages)
    return out[:max_chars]
