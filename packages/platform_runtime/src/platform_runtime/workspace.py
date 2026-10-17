"""Single-host workspace with immutable files, CAS revisions and SQLite run states."""

from __future__ import annotations

import json
import os
import re
import sqlite3
from collections.abc import Callable
from hashlib import file_digest, sha256
from math import isfinite
from pathlib import Path
from typing import BinaryIO, Literal
from uuid import uuid4

from tool_contracts.api import (
    AssetRef,
    DocumentRevision,
    DraftSnapshot,
    ProcessExitReceipt,
    RecoveryReport,
    RunRecord,
    WorkspaceFormat,
    validate_relative_path,
)

MAX_DOCUMENT_BYTES = 16 * 1024 * 1024
Checkpoint = Literal["before_publish", "after_publish", "before_database_commit"]


class WorkspaceError(RuntimeError):
    """Workspace operation failed without claiming a successful result."""


class WorkspaceBusy(WorkspaceError):
    """Another host owns this workspace."""


class IntegrityError(WorkspaceError):
    """A declared asset or workspace path failed validation."""


class StateConflict(WorkspaceError):
    """An old revision, cancellation, or terminal state forbids this update."""


def _plain(path: Path) -> None:
    for item in (path, *path.parents):
        if item.is_symlink() or item.is_junction():
            raise IntegrityError("不支持工作区或输入路径中的符号链接/重解析点")


class OwnerLock:
    def __init__(self, path: Path) -> None:
        _plain(path)
        self.stream: BinaryIO = path.open("a+b")
        if path.stat().st_size == 0:
            self.stream.write(b"0")
            self.stream.flush()
        self.stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self.stream.close()
            raise WorkspaceBusy("该工作区已由另一宿主打开") from exc

    def close(self) -> None:
        if self.stream.closed:
            return
        self.stream.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(self.stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
        self.stream.close()


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("文档包含重复 JSON 字段")
        result[key] = value
    return result


def _finite_float(value: str) -> float:
    result = float(value)
    if not isfinite(result):
        raise ValueError("文档不能包含非有限数")
    return result


def _constant(value: str) -> object:
    raise ValueError("文档不能包含非有限数：" + value)


def _document(data: bytes) -> None:
    if not data or len(data) > MAX_DOCUMENT_BYTES:
        raise WorkspaceError("JSON 文档为空或超过容量")
    try:
        value: object = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_float=_finite_float,
            parse_constant=_constant,
        )
    except (ValueError, RecursionError) as exc:
        raise WorkspaceError("文档不是有效、有限、无重复字段的 UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise WorkspaceError("文档须为 JSON 对象")


class Workspace:
    """Thread-affine host storage; commands must run on the owning storage thread."""

    def __init__(
        self,
        root: Path,
        *,
        initialize: bool,
        fault_hook: Callable[[Checkpoint], None] | None = None,
    ) -> None:
        root = root.absolute()
        _plain(root)
        self.root = root.resolve()
        self._closed = False
        self._fault_hook = fault_hook
        self._owner = OwnerLock(self._path(".owner.lock"))
        self.recovery = RecoveryReport()
        self._db: sqlite3.Connection
        try:
            if initialize:
                header = WorkspaceFormat(
                    format="bioimage-workspace", version=1, workspace_id=uuid4().hex
                )
                with self._path("workspace.json").open("xb") as stream:
                    stream.write(header.model_dump_json().encode("utf-8"))
                    stream.flush()
                    os.fsync(stream.fileno())
                for name in ("assets", "drafts", "runs", "results", ".staging", "recovery"):
                    self._path(name).mkdir()
                self._db = sqlite3.connect(self._path("metadata.sqlite"))
                self._db.executescript("""
                    PRAGMA user_version=1;
                    CREATE TABLE metadata (workspace_id TEXT PRIMARY KEY);
                    CREATE TABLE assets (asset_id TEXT PRIMARY KEY,
                                         relative_path TEXT UNIQUE NOT NULL,
                                         record_json TEXT NOT NULL);
                    CREATE TABLE documents (document_id TEXT PRIMARY KEY, tool_id TEXT NOT NULL,
                                            current_revision INTEGER NOT NULL);
                    CREATE TABLE drafts (document_id TEXT NOT NULL, revision INTEGER NOT NULL,
                                         record_json TEXT NOT NULL,
                                         PRIMARY KEY(document_id,revision));
                    CREATE TABLE runs (run_id TEXT PRIMARY KEY, state TEXT NOT NULL,
                                       document_id TEXT NOT NULL,
                                       record_json TEXT NOT NULL);
                """)
                self._db.execute("INSERT INTO metadata VALUES (?)", (header.workspace_id,))
                self._db.commit()
            else:
                header = WorkspaceFormat.model_validate_json(
                    self._path("workspace.json").read_bytes()
                )
                uri = self._path("metadata.sqlite").as_uri() + "?mode=rw"
                self._db = sqlite3.connect(uri, uri=True)
                if self._db.execute("PRAGMA user_version").fetchone()[0] != 1:
                    raise WorkspaceError("未知工作区数据库版本；不自动迁移")
                if self._db.execute("SELECT workspace_id FROM metadata").fetchone() != (
                    header.workspace_id,
                ):
                    raise IntegrityError("工作区标识与数据库不一致")
            self._db.row_factory = sqlite3.Row
            self.recovery = self._recover() if not initialize else RecoveryReport()
        except (OSError, ValueError, sqlite3.Error, WorkspaceError):
            if hasattr(self, "_db"):
                self._db.close()
            self._owner.close()
            raise

    @classmethod
    def create(
        cls, root: str | Path, *, fault_hook: Callable[[Checkpoint], None] | None = None
    ) -> Workspace:
        path = Path(root).absolute()
        _plain(path)
        if path.exists() and (not path.is_dir() or any(path.iterdir())):
            raise WorkspaceError("新工作区须使用不存在或空的目录，不能覆盖已有数据")
        path.mkdir(parents=True, exist_ok=True)
        return cls(path, initialize=True, fault_hook=fault_hook)

    @classmethod
    def open(
        cls, root: str | Path, *, fault_hook: Callable[[Checkpoint], None] | None = None
    ) -> Workspace:
        path = Path(root).absolute()
        _plain(path)
        if not path.is_dir() or not (path / "workspace.json").is_file():
            raise WorkspaceError("不是已创建的工作区")
        return cls(path, initialize=False, fault_hook=fault_hook)

    def __enter__(self) -> Workspace:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if not self._closed:
            self._db.close()
            self._owner.close()
            self._closed = True

    def _path(self, relative: str) -> Path:
        if self._closed:
            raise WorkspaceError("工作区已关闭")
        try:
            validate_relative_path(relative)
        except ValueError as exc:
            raise IntegrityError("工作区路径越界或含非法别名") from exc
        path = self.root.joinpath(*relative.split("/"))
        _plain(path)
        if not path.resolve().is_relative_to(self.root):
            raise IntegrityError("工作区路径越界")
        if path.is_file() and path.stat().st_nlink != 1:
            raise IntegrityError("工作区文件不能为外部硬链接")
        return path

    def _checkpoint(self, name: Checkpoint) -> None:
        if self._fault_hook:
            self._fault_hook(name)

    def _publish(
        self, category: str, directory: str, leaf: str, write: Callable[[BinaryIO], None]
    ) -> AssetRef:
        asset_id = uuid4().hex
        stage = self._path(".staging/" + asset_id)
        stage.mkdir()
        payload = stage / leaf
        with payload.open("xb") as stream:
            write(stream)
            stream.flush()
            os.fsync(stream.fileno())
        with payload.open("rb") as stream:
            digest = file_digest(stream, "sha256").hexdigest()
        relative = f"{category}/{directory}/{leaf}"
        ref = AssetRef(
            asset_id=asset_id,
            relative_path=relative,
            sha256=digest,
            size_bytes=payload.stat().st_size,
        )
        with (stage / "asset.json").open("xb") as stream:
            stream.write(ref.model_dump_json().encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        self._checkpoint("before_publish")
        self._check_files(
            ref,
            self._path(f".staging/{asset_id}/{leaf}"),
            self._path(f".staging/{asset_id}/asset.json"),
        )
        target = self._path(f"{category}/{directory}")
        if target.exists():
            raise IntegrityError("资产目录已存在，禁止覆盖")
        stage.rename(target)
        self._checkpoint("after_publish")
        self._verify_file(ref)
        return ref

    def _blob(self, category: str, directory: str, leaf: str, data: bytes) -> AssetRef:
        def write(stream: BinaryIO) -> None:
            stream.write(data)

        return self._publish(category, directory, leaf, write)

    def _insert_asset(self, ref: AssetRef) -> None:
        self._db.execute(
            "INSERT INTO assets VALUES (?,?,?)",
            (ref.asset_id, ref.relative_path, ref.model_dump_json()),
        )

    def import_asset(self, source: str | Path, expected_sha256: str) -> AssetRef:
        path = Path(source).absolute()
        _plain(path)
        if not path.is_file() or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
            raise IntegrityError("输入文件或来源摘要无效")
        suffix = path.suffix.lower()
        if suffix and not re.fullmatch(r"\.[a-z0-9]{1,16}", suffix):
            raise IntegrityError("输入扩展名包含非法路径成分")

        def write(stream: BinaryIO) -> None:
            digest = sha256()
            with path.open("rb") as original:
                while chunk := original.read(1024 * 1024):
                    digest.update(chunk)
                    stream.write(chunk)
            if digest.hexdigest() != expected_sha256:
                raise IntegrityError("输入快照与声明的来源摘要不符")

        ref = self._publish("assets", uuid4().hex, "source" + suffix, write)
        self._checkpoint("before_database_commit")
        self._verify_file(ref)
        with self._db:
            self._insert_asset(ref)
        return ref

    def get_asset(self, asset_id: str) -> AssetRef:
        row = self._db.execute(
            "SELECT relative_path,record_json FROM assets WHERE asset_id=?", (asset_id,)
        ).fetchone()
        if row is None:
            raise IntegrityError("资产未登记")
        ref = AssetRef.model_validate_json(row[1])
        if ref.asset_id != asset_id or ref.relative_path != row[0]:
            raise IntegrityError("资产登记身份不一致")
        return ref

    def asset_path(self, ref: AssetRef) -> Path:
        if self.get_asset(ref.asset_id) != ref:
            raise IntegrityError("资产引用与登记内容不一致")
        return self._verify_file(ref)

    def _verify_file(self, ref: AssetRef) -> Path:
        path = self._path(ref.relative_path)
        manifest_path = self._path(ref.relative_path.rsplit("/", 1)[0] + "/asset.json")
        return self._check_files(ref, path, manifest_path)

    def _check_files(self, ref: AssetRef, path: Path, manifest_path: Path) -> Path:
        if (
            not manifest_path.is_file()
            or AssetRef.model_validate_json(manifest_path.read_bytes()) != ref
        ):
            raise IntegrityError("资产发布清单与登记不一致")
        if not path.is_file() or path.stat().st_size != ref.size_bytes:
            raise IntegrityError("资产缺失或大小改变")
        with path.open("rb") as stream:
            if file_digest(stream, "sha256").hexdigest() != ref.sha256:
                raise IntegrityError("资产摘要改变")
        return path

    def read_asset(self, ref: AssetRef, *, max_bytes: int = MAX_DOCUMENT_BYTES) -> bytes:
        if type(max_bytes) is not int or max_bytes < 0 or ref.size_bytes > max_bytes:
            raise WorkspaceError("资产超过读取预算，应使用文件路径端口")
        data = self.asset_path(ref).read_bytes()
        if len(data) != ref.size_bytes or sha256(data).hexdigest() != ref.sha256:
            raise IntegrityError("读取期间资产改变")
        return data

    def save_draft(
        self,
        document_id: str,
        tool_id: str,
        revision: int,
        data: bytes,
        *,
        expected_previous_revision: int | None,
    ) -> DraftSnapshot:
        DocumentRevision(document_id=document_id, tool_id=tool_id, revision=revision)
        if expected_previous_revision is not None and type(expected_previous_revision) is not int:
            raise StateConflict("期望修订必须为整数，不能是布尔值")
        _document(data)
        row = self._db.execute(
            "SELECT tool_id,current_revision FROM documents WHERE document_id=?", (document_id,)
        ).fetchone()
        if row is None:
            if expected_previous_revision is not None or revision != 0:
                raise StateConflict("新草稿须从修订 0 开始")
        elif row[0] != tool_id or row[1] != expected_previous_revision or revision != row[1] + 1:
            raise StateConflict("草稿修订已改变，不能覆盖旧草稿")
        ref = self._blob("drafts", uuid4().hex, "document.json", data)
        snapshot = DraftSnapshot(
            document_id=document_id, tool_id=tool_id, revision=revision, asset=ref
        )
        self._checkpoint("before_database_commit")
        self._verify_file(ref)
        with self._db:
            self._insert_asset(ref)
            self._db.execute(
                "INSERT INTO drafts VALUES (?,?,?)",
                (document_id, revision, snapshot.model_dump_json()),
            )
            if row is None:
                self._db.execute(
                    "INSERT INTO documents VALUES (?,?,?)", (document_id, tool_id, revision)
                )
            else:
                changed = self._db.execute(
                    "UPDATE documents SET current_revision=? "
                    "WHERE document_id=? AND current_revision=?",
                    (revision, document_id, expected_previous_revision),
                ).rowcount
                if changed != 1:
                    raise StateConflict("草稿 CAS 失败")
        return snapshot

    def load_draft(self, document_id: str, revision: int | None = None) -> DraftSnapshot:
        if revision is None:
            row = self._db.execute(
                "SELECT current_revision FROM documents WHERE document_id=?", (document_id,)
            ).fetchone()
            if row is None:
                raise WorkspaceError("草稿不存在")
            revision = row[0]
        row = self._db.execute(
            "SELECT record_json FROM drafts WHERE document_id=? AND revision=?",
            (document_id, revision),
        ).fetchone()
        if row is None:
            raise WorkspaceError("草稿修订不存在")
        snapshot = DraftSnapshot.model_validate_json(row[0])
        if snapshot.document_id != document_id or snapshot.revision != revision:
            raise IntegrityError("草稿登记身份不一致")
        self.asset_path(snapshot.asset)
        return snapshot

    def prepare_run(self, document_id: str, revision: int | None = None) -> RunRecord:
        draft = self.load_draft(document_id, revision)
        run_id = uuid4().hex
        ref = self._blob("runs", run_id, "request.json", self.read_asset(draft.asset))
        run = RunRecord(
            run_id=run_id,
            document_id=document_id,
            tool_id=draft.tool_id,
            revision=draft.revision,
            state="prepared",
            request=ref,
        )
        self._checkpoint("before_database_commit")
        self._verify_file(ref)
        with self._db:
            self._insert_asset(ref)
            self._db.execute(
                "INSERT INTO runs VALUES (?,?,?,?)",
                (run_id, run.state, run.document_id, run.model_dump_json()),
            )
        return run

    def get_run(self, run_id: str) -> RunRecord:
        row = self._db.execute(
            "SELECT state,document_id,record_json FROM runs WHERE run_id=?", (run_id,)
        ).fetchone()
        if row is None:
            raise WorkspaceError("运行不存在")
        run = RunRecord.model_validate_json(row[2])
        if run.run_id != run_id or run.state != row[0] or run.document_id != row[1]:
            raise IntegrityError("运行登记身份或状态不一致")
        self.asset_path(run.request)
        if run.result is not None:
            self.asset_path(run.result)
        return run

    def list_documents(self) -> tuple[DraftSnapshot, ...]:
        rows = self._db.execute("SELECT document_id FROM documents ORDER BY rowid DESC").fetchall()
        return tuple(self.load_draft(row[0]) for row in rows)

    def list_runs(self, document_id: str | None = None) -> tuple[RunRecord, ...]:
        if document_id is None:
            rows = self._db.execute("SELECT run_id FROM runs ORDER BY rowid DESC").fetchall()
        else:
            rows = self._db.execute(
                "SELECT run_id FROM runs WHERE document_id=? ORDER BY rowid DESC", (document_id,)
            ).fetchall()
        return tuple(self.get_run(row[0]) for row in rows)

    def backup(self, destination: str | Path) -> Path:
        """Copy immutable files and use SQLite's consistent backup API at a quiescent point."""
        target = Path(destination).absolute()
        _plain(target)
        resolved = target.resolve()
        if target.exists() or resolved.is_relative_to(self.root) or self._db.in_transaction:
            raise WorkspaceError("备份须使用工作区外的新目录，且不能在活动存储事务内执行")
        for row in self._db.execute("SELECT asset_id FROM assets").fetchall():
            self.asset_path(self.get_asset(row[0]))
        header = WorkspaceFormat.model_validate_json(self._path("workspace.json").read_bytes())
        if self._db.execute("PRAGMA user_version").fetchone()[0] != 1:
            raise WorkspaceError("未知数据库版本不能备份为当前格式")
        target.mkdir(parents=True)
        (target / "workspace.json").write_text(header.model_dump_json(), encoding="utf-8")
        for category in ("assets", "drafts", "runs", "results", ".staging", "recovery"):
            (target / category).mkdir()
            for entry in self._path(category).rglob("*"):
                relative = entry.relative_to(self.root).as_posix()
                source = self._path(relative)
                copied = target.joinpath(*relative.split("/"))
                _plain(copied)
                if not copied.resolve().is_relative_to(resolved):
                    raise IntegrityError("备份路径越界")
                if source.is_dir():
                    copied.mkdir(exist_ok=True)
                elif source.is_file():
                    with source.open("rb") as original, copied.open("xb") as output:
                        while chunk := original.read(1024 * 1024):
                            output.write(chunk)
                        output.flush()
                        os.fsync(output.fileno())
                else:
                    raise IntegrityError("工作区含未知文件类型")
        connection = sqlite3.connect(target / "metadata.sqlite")
        try:
            self._db.backup(connection)
        finally:
            connection.close()
        return target

    def _update_run(self, old: RunRecord, new: RunRecord) -> None:
        RunRecord.model_validate_json(new.model_dump_json())
        changed = self._db.execute(
            "UPDATE runs SET state=?,record_json=? WHERE run_id=? AND state=?",
            (new.state, new.model_dump_json(), old.run_id, old.state),
        ).rowcount
        if changed != 1:
            raise StateConflict("运行状态已改变，拒绝旧终态")

    def start_run(self, run_id: str, pid: int) -> RunRecord:
        old = self.get_run(run_id)
        if old.state != "prepared":
            raise StateConflict("运行不能重复启动")
        new = old.model_copy(update={"state": "running", "pid": pid})
        with self._db:
            active = self._db.execute(
                "SELECT record_json FROM runs WHERE state IN ('running','cancelling','committing')"
            ).fetchall()
            if any(RunRecord.model_validate_json(row[0]).pid is not None for row in active):
                raise StateConflict("当前工作区只允许一个活动计算进程")
            self._update_run(old, new)
        return new

    def request_cancel(self, run_id: str) -> RunRecord:
        old = self.get_run(run_id)
        if old.state not in ("prepared", "running", "committing"):
            raise StateConflict("终态或重复取消不能改写")
        new = old.model_copy(update={"state": "cancelling"})
        with self._db:
            self._update_run(old, new)
        return new

    @staticmethod
    def _exit(run: RunRecord, receipt: ProcessExitReceipt) -> None:
        if receipt.run_id != run.run_id or receipt.pid != (run.pid or 0):
            raise StateConflict("退出回执不属于当前运行进程")

    def finish_cancelled(self, run_id: str, receipt: ProcessExitReceipt) -> RunRecord:
        old = self.get_run(run_id)
        self._exit(old, receipt)
        if old.state != "cancelling":
            raise StateConflict("未请求取消或运行已结束")
        new = old.model_copy(update={"state": "cancelled"})
        with self._db:
            self._update_run(old, new)
        return new

    def finish_failure(
        self, run_id: str, receipt: ProcessExitReceipt, *, reason: str, interrupted: bool = False
    ) -> RunRecord:
        old = self.get_run(run_id)
        self._exit(old, receipt)
        if old.state not in ("prepared", "running", "committing") or not reason:
            raise StateConflict("运行状态或失败原因无效")
        new = old.model_copy(
            update={"state": "interrupted" if interrupted else "failed", "reason": reason}
        )
        with self._db:
            self._update_run(old, new)
        return new

    def commit_result(
        self,
        run_id: str,
        receipt: ProcessExitReceipt,
        data: bytes,
        *,
        cancelled: Callable[[], bool] | None = None,
    ) -> RunRecord:
        _document(data)
        old = self.get_run(run_id)
        self._exit(old, receipt)
        if old.state != "running" or receipt.exit_code != 0 or receipt.pid == 0:
            raise StateConflict("仅已确认成功退出的运行可以提交结果")
        if cancelled is not None and cancelled():
            self.request_cancel(run_id)
            raise StateConflict("提交前已请求取消")
        self.asset_path(old.request)
        committing = old.model_copy(update={"state": "committing"})
        with self._db:
            self._update_run(old, committing)
        ref = self._blob("results", run_id, "result.json", data)
        self._checkpoint("before_database_commit")
        self._verify_file(ref)
        if cancelled is not None and cancelled():
            self.request_cancel(run_id)
            raise StateConflict("发布后提交前已请求取消")
        completed = committing.model_copy(update={"state": "succeeded", "result": ref})
        with self._db:
            self._insert_asset(ref)
            self._update_run(committing, completed)
        return completed

    def _recover(self) -> RecoveryReport:
        interrupted: list[str] = []
        rows = self._db.execute(
            "SELECT run_id FROM runs "
            "WHERE state IN ('prepared','running','committing','cancelling')"
        ).fetchall()
        with self._db:
            for row in rows:
                old = self.get_run(row[0])
                new = old.model_copy(
                    update={
                        "state": "interrupted",
                        "reason": "宿主退出或提交未完成，重启后状态未知",
                    }
                )
                self._update_run(old, new)
                interrupted.append(old.run_id)
        quarantined: list[str] = []
        for item in self._path(".staging").iterdir():
            source = self._path(".staging/" + item.name)
            relative = "recovery/" + uuid4().hex
            source.rename(self._path(relative))
            quarantined.append(relative)
        registered = {row[0] for row in self._db.execute("SELECT relative_path FROM assets")}
        orphans: list[str] = []
        for category in ("assets", "drafts", "runs", "results"):
            for directory in self._path(category).iterdir():
                target = self._path(category + "/" + directory.name)
                manifest = target / "asset.json"
                _plain(manifest)
                if not manifest.is_file():
                    raise IntegrityError("发布目录缺少资产清单")
                ref = AssetRef.model_validate_json(manifest.read_bytes())
                if ref.relative_path.rsplit("/", 1)[0] != f"{category}/{directory.name}":
                    raise IntegrityError("资产清单位置与发布目录不符")
                if ref.relative_path not in registered:
                    orphans.append(category + "/" + directory.name)
                elif self.get_asset(ref.asset_id) != ref:
                    raise IntegrityError("资产发布清单与数据库不一致")
        return RecoveryReport(
            interrupted_run_ids=tuple(interrupted),
            quarantined_paths=tuple(quarantined),
            orphan_paths=tuple(orphans),
        )
