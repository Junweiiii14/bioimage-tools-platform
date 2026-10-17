"""Schema, format marker and identity commit together, including real SQL failure."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from platform_runtime.api import Workspace, WorkspaceError


def test_failed_identity_insert_rolls_back_schema_and_releases_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "failed-new-workspace"
    original_connect = sqlite3.connect

    def authorize(
        action: int,
        table: str | None,
        column: str | None,
        database: str | None,
        trigger: str | None,
    ) -> int:
        return (
            sqlite3.SQLITE_DENY
            if action == sqlite3.SQLITE_INSERT and table == "metadata"
            else sqlite3.SQLITE_OK
        )

    def connect(database: str | Path, *, uri: bool = False) -> sqlite3.Connection:
        connection = original_connect(database, uri=uri)
        connection.set_authorizer(authorize)
        return connection

    with monkeypatch.context() as patch:
        patch.setattr(sqlite3, "connect", connect)
        with pytest.raises(sqlite3.DatabaseError, match="not authorized"):
            Workspace.create(root)
    with closing(original_connect(root / "metadata.sqlite")) as database:
        assert database.execute("PRAGMA user_version").fetchone() == (0,)
        assert (
            database.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == []
        )
    # An acquired/released owner lock reaches format validation, rather than reporting busy.
    with pytest.raises(WorkspaceError, match="未知工作区数据库版本"):
        Workspace.open(root)
    assert (root / "workspace.json").is_file()  # Failed creation evidence is preserved.
