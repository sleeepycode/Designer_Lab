import json
from pathlib import Path


def save_report(path: str, data: dict) -> None:
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
