from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List

from .units import SpeedResult

HISTORY_FILE = Path.home() / ".speedtest_history.json"
HISTORY_LIMIT = 10


def load_history() -> List[SpeedResult]:
    if not HISTORY_FILE.exists():
        return []
    try:
        data = json.loads(HISTORY_FILE.read_text())
        return [SpeedResult.from_dict(item) for item in data][-HISTORY_LIMIT:]
    except Exception:
        return []


def save_result(result: SpeedResult) -> None:
    history = load_history()
    history.append(result)
    trimmed = history[-HISTORY_LIMIT:]
    payload = [entry.to_dict() for entry in trimmed]
    HISTORY_FILE.write_text(json.dumps(payload, indent=2))


def export_history(path: Path) -> None:
    history = [entry.to_dict() for entry in load_history()]
    payload = {"exported_at": datetime.utcnow().isoformat(), "results": history}
    path.write_text(json.dumps(payload, indent=2))
