"""
config.py — one place for file paths and settings.

Settings come from your .env file (never committed to GitHub), so your API key
stays private and you can switch models without editing code.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
AD_DIRS = {"FAA": DATA_DIR / "faa", "EASA": DATA_DIR / "easa"}
REGS_DIR = DATA_DIR / "regs"
FLEET_FILE = DATA_DIR / "fleet.json"
EXTRACTED_FILE = DATA_DIR / "extracted.json"
INDEX_DIR = ROOT / "index_store"
PROMPTS_DIR = ROOT / "prompts"
AUDIT_FILE = ROOT / "audit_log.jsonl"

# Cheaper, faster model for the repetitive extraction job.
EXTRACT_MODEL = os.getenv("EXTRACT_MODEL", "claude-haiku-4-5-20251001")
# Stronger model for analysis and safety review.
REASON_MODEL = os.getenv("REASON_MODEL", "claude-sonnet-5-5")

PROMPT_VERSIONS = {
    "extractor": os.getenv("EXTRACTOR_PROMPT", "extractor_v1"),
    "analyst": os.getenv("ANALYST_PROMPT", "analyst_v1"),
    "reviewer": os.getenv("REVIEWER_PROMPT", "reviewer_v1"),
}

MAX_RETRIES = 2          # how many times the Analyst may rewrite after review
MAX_ADS_TO_ANALYZE = 8   # caps cost per question


def load_prompt(role: str) -> str:
    return (PROMPTS_DIR / f"{PROMPT_VERSIONS[role]}.md").read_text(encoding="utf-8")
