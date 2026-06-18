"""Shared workflow helpers for markdown artifacts and logs."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from config import LOGS


def read_markdown_with_frontmatter(file_path: Path) -> tuple[dict[str, Any], str]:
    raw = Path(file_path).read_text(encoding="utf-8")
    if not raw.startswith("---"):
        return {}, raw.strip()

    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}, raw.strip()

    try:
        frontmatter = yaml.safe_load(parts[1].strip()) or {}
    except yaml.YAMLError:
        return {}, raw.strip()

    return frontmatter, parts[2].strip()


def write_markdown_with_frontmatter(
    file_path: Path,
    frontmatter: dict[str, Any],
    body: str,
) -> Path:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    content = [
        "---",
        yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip(),
        "---",
        "",
        body.strip(),
        "",
    ]
    file_path.write_text("\n".join(content), encoding="utf-8")
    return file_path


def extract_email_address(value: str) -> str:
    match = re.search(r"<([^<>@\s]+@[^<>\s]+)>", value or "")
    if match:
        return match.group(1).strip()

    match = re.search(r"([^<>\s]+@[^<>\s]+)", value or "")
    if match:
        return match.group(1).strip()

    return (value or "").strip()


def move_file(source_path: Path, destination_dir: Path) -> Path:
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / source_path.name
    shutil.move(str(source_path), str(destination))
    return destination


def append_log(action: str, filename: str, details: dict[str, Any] | None = None) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    log_file = LOGS / f"{datetime.now().strftime('%Y-%m-%d')}.json"

    entries: list[dict[str, Any]] = []
    if log_file.exists():
        try:
            parsed = json.loads(log_file.read_text(encoding="utf-8") or "[]")
            if isinstance(parsed, list):
                entries = parsed
        except (json.JSONDecodeError, OSError):
            entries = []

    entries.append(
        {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "filename": filename,
            "details": details or {},
        }
    )
    log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def unique_path(directory: Path, filename: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    candidate = directory / filename
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    counter = 2
    while True:
        next_candidate = directory / f"{stem}_{counter}{suffix}"
        if not next_candidate.exists():
            return next_candidate
        counter += 1
