"""Local selection memory; original paths never travel inside project archives."""

import json
import os
from hashlib import sha256
from pathlib import Path

from PySide6.QtCore import QSettings


def origin_key(workspace: str, project_id: str, row_id: str, source_sha256: str) -> str:
    identity = (
        os.path.normcase(str(Path(workspace).absolute())),
        project_id,
        row_id,
        source_sha256,
    )
    return "source_origins/" + sha256(json.dumps(identity).encode("utf-8")).hexdigest()


class SourceOrigins:
    def __init__(self, settings: QSettings | None = None) -> None:
        self.settings = (
            settings if settings is not None else QSettings("BioImageTools", "SourceOrigins")
        )

    def remember(
        self, workspace: str, project_id: str, row_id: str, source_sha256: str, selected_path: str
    ) -> None:
        self.settings.setValue(
            origin_key(workspace, project_id, row_id, source_sha256),
            str(Path(selected_path).absolute()),
        )

    def lookup(self, workspace: str, project_id: str, row_id: str, source_sha256: str) -> str:
        value = self.settings.value(origin_key(workspace, project_id, row_id, source_sha256), "")
        return value if isinstance(value, str) else ""
