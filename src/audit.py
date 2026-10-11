"""
audit.py — writes one line per step to audit_log.jsonl.

In aviation, "who decided what, based on which evidence, when" must be traceable.
Each line records the step, the model and prompt version used, and its inputs/outputs.
JSONL = one JSON object per line, easy to search and load later.
"""
import json
from datetime import datetime, timezone

from . import config


def log_event(run_id: str, step: str, data: dict, path=None) -> None:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "step": step,
        **data,
    }
    with open(path or config.AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")
