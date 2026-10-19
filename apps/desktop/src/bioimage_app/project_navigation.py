"""Versioned local navigation memory, separate from scientific project documents."""

import json
import os
from hashlib import sha256
from pathlib import Path
from typing import cast

from PySide6.QtCore import QSettings

MODES = frozenset({"review", "layout", "quant", "results"})


class ProjectNavigation:
    def __init__(self, settings: QSettings) -> None:
        self.settings = settings

    @staticmethod
    def key(workspace: str) -> str:
        normalized = os.path.normcase(str(Path(workspace).resolve()))
        return "navigation_v1/" + sha256(normalized.encode("utf-8")).hexdigest()

    def read(self, workspace: str) -> dict[str, object]:
        raw = self.settings.value(self.key(workspace), "{}")
        try:
            result: object = json.loads(raw) if isinstance(raw, str) else {}
        except (ValueError, TypeError):
            return {}
        return cast(dict[str, object], result) if isinstance(result, dict) else {}

    def remember(self, workspace: str, position: dict[str, object]) -> None:
        mode = position.get("mode")
        if not workspace or not isinstance(mode, str) or mode not in MODES:
            return
        allowed = {"projectId", "mode", "rowId", "figure", "lane", "name"}
        record = {key: value for key, value in position.items() if key in allowed}
        self.settings.setValue(self.key(workspace), json.dumps(record, ensure_ascii=False))
        recents = self.recent()
        recents = [item for item in recents if item.get("path") != workspace]
        recents.insert(0, {"path": workspace, **record})
        self.settings.setValue("recent_projects_v1", json.dumps(recents[:12], ensure_ascii=False))
        self.settings.sync()

    def recent(self) -> list[dict[str, object]]:
        raw = self.settings.value("recent_projects_v1", "[]")
        try:
            records: object = json.loads(raw) if isinstance(raw, str) else []
        except (ValueError, TypeError):
            return []
        if not isinstance(records, list):
            return []
        entries = cast(list[object], records)
        return [
            cast(dict[str, object], r)
            for r in entries
            if isinstance(r, dict) and isinstance(cast(dict[str, object], r).get("path"), str)
        ][:12]
