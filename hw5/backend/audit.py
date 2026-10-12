import json
from pathlib import Path
from typing import Any


AUDIT_FILE = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"


def append_audit(event: dict[str, Any]) -> None:
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict[str, Any]] = []
    if AUDIT_FILE.exists() and AUDIT_FILE.stat().st_size:
        existing = json.loads(AUDIT_FILE.read_text(encoding="utf-8"))
    existing.append(event)
    AUDIT_FILE.write_text(json.dumps(existing, indent=2, default=str) + "\n", encoding="utf-8")
