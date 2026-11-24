"""Shared CSV storage helpers for the local demo data files in data/."""

from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_csv(path: Path, fields: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [{key: (row.get(key) or "") for key in fields} for row in csv.DictReader(handle)]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})
    os.replace(tmp, path)


def next_sequential_id(prefix: str, rows: list[dict[str, str]], field: str) -> str:
    """Return the next ``PREFIX-001`` style id, based on the highest existing number."""
    numbers = [
        int(row[field].split("-")[-1])
        for row in rows
        if row.get(field, "").startswith(f"{prefix}-") and row[field].split("-")[-1].isdigit()
    ]
    return f"{prefix}-{max(numbers, default=0) + 1:03d}"
