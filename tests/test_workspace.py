"""Real filesystem/SQLite transactions and fault recovery through public APIs."""

import json
import os
import sqlite3
import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from typing import Literal

import numpy as np
import pytest
import tifffile
from platform_runtime.api import (
    IntegrityError,
    StateConflict,
    Workspace,
    WorkspaceBusy,
    WorkspaceError,
)
from pydantic import ValidationError
from tool_contracts.api import AssetRef, ProcessExitReceipt, storage_contract_schema
from wb_tool.api import (
    AnalysisRequest,
    BandAnnotation,
    BandBounds,
    LaneAnnotation,
    LaneROI,
    ResultFrame,
    StartFrame,
    WorkerConversation,
    encode_worker_frame,
    load_tiff,
)


@pytest.fixture
def workspace(tmp_path: Path):
    with Workspace.create(tmp_path / "工作区") as store:
        yield store


def prepare(store: Workspace) -> str:
    store.save_draft("document", "wb", 0, b'{"parameters":1}', expected_previous_revision=None)
    return store.prepare_run("document").run_id


def receipt(run_id: str, *, code: int = 0) -> ProcessExitReceipt:
    return ProcessExitReceipt(run_id=run_id, pid=123, exit_code=code)


def test_import_snapshot_and_original_unchanged(workspace: Workspace, tmp_path: Path) -> None:
    source = tmp_path / "original.tif"
    original = b"original quantitative source"
    source.write_bytes(original)
    ref = workspace.import_asset(source, sha256(original).hexdigest())
    assert workspace.read_asset(ref) == original
    assert source.read_bytes() == original
    source.write_bytes(b"external edit after import")
    assert workspace.read_asset(ref) == original


def test_draft_history_cas_and_run_snapshot(workspace: Workspace) -> None:
    first = workspace.save_draft("D", "wb", 0, b'{"revision":0}', expected_previous_revision=None)
    run = workspace.prepare_run("D")
    second = workspace.save_draft("D", "wb", 1, b'{"revision":1}', expected_previous_revision=0)
    assert workspace.read_asset(first.asset) == b'{"revision":0}'
    assert workspace.read_asset(second.asset) == b'{"revision":1}'
    assert workspace.read_asset(run.request) == b'{"revision":0}'
    assert workspace.load_draft("D").revision == 1
    assert workspace.load_draft("D", 0) == first
    assert workspace.prepare_run("D", 0).revision == 0
    with pytest.raises(StateConflict):
        workspace.save_draft("D", "wb", 1, b"{}", expected_previous_revision=0)
    with pytest.raises(StateConflict):
        workspace.save_draft("D", "wb", 2, b"{}", expected_previous_revision=False)
    assert len(workspace.list_documents()) == 1


def test_result_commit_requires_exit_and_is_immutable(workspace: Workspace) -> None:
    run_id = prepare(workspace)
    with pytest.raises(StateConflict):
        workspace.commit_result(run_id, receipt(run_id), b'{"signal":10}')
    workspace.start_run(run_id, 123)
    with pytest.raises(StateConflict):
        workspace.commit_result(run_id, receipt(run_id, code=2), b'{"signal":10}')
    done = workspace.commit_result(run_id, receipt(run_id), b'{"signal":10}')
    assert done.state == "succeeded" and done.result is not None
    assert workspace.read_asset(done.result) == b'{"signal":10}'
    with pytest.raises(StateConflict):
        workspace.commit_result(run_id, receipt(run_id), b'{"signal":999}')
    with pytest.raises(StateConflict):
        workspace.request_cancel(run_id)
    assert workspace.list_runs("document") == (done,)


def test_cancel_prevents_success_and_needs_matching_exit(workspace: Workspace) -> None:
    run_id = prepare(workspace)
    workspace.start_run(run_id, 123)
    workspace.request_cancel(run_id)
    assert workspace.get_run(run_id).state == "cancelling"
    with pytest.raises(StateConflict):
        workspace.finish_cancelled(run_id, ProcessExitReceipt(run_id=run_id, pid=456, exit_code=0))
    with pytest.raises(StateConflict):
        workspace.commit_result(run_id, receipt(run_id), b"{}")
    assert workspace.finish_cancelled(run_id, receipt(run_id, code=-9)).state == "cancelled"


def test_cancel_before_launch(workspace: Workspace) -> None:
    run_id = prepare(workspace)
    workspace.request_cancel(run_id)
    no_process = ProcessExitReceipt(run_id=run_id, pid=0, exit_code=None)
    assert workspace.finish_cancelled(run_id, no_process).state == "cancelled"


def test_one_active_process_budget(workspace: Workspace) -> None:
    first = prepare(workspace)
    second = workspace.prepare_run("document")
    workspace.start_run(first, 123)
    with pytest.raises(StateConflict):
        workspace.start_run(second.run_id, 456)
    workspace.finish_failure(first, receipt(first, code=2), reason="worker failed")
    assert workspace.start_run(second.run_id, 456).state == "running"


def test_workspace_exclusive_owner_and_unknown_version(tmp_path: Path) -> None:
    root = tmp_path / "root"
    with Workspace.create(root), pytest.raises(WorkspaceBusy):
        Workspace.open(root)
    with sqlite3.connect(root / "metadata.sqlite") as database:
        database.execute("PRAGMA user_version=999")
    with pytest.raises(WorkspaceError, match="版本"):
        Workspace.open(root)


def test_restart_marks_only_nonterminal_interrupted(tmp_path: Path) -> None:
    root = tmp_path / "root"
    with Workspace.create(root) as store:
        done_id = prepare(store)
        store.start_run(done_id, 123)
        done = store.commit_result(done_id, receipt(done_id), b'{"signal":10}')
        pending = store.prepare_run("document").run_id
        store.start_run(pending, 456)
    with Workspace.open(root) as store:
        assert store.recovery.interrupted_run_ids == (pending,)
        assert store.get_run(pending).state == "interrupted"
        assert store.get_run(done_id) == done
    with Workspace.open(root) as store:
        assert store.recovery.interrupted_run_ids == ()


@pytest.mark.parametrize(
    "checkpoint", ["before_publish", "after_publish", "before_database_commit"]
)
def test_result_failure_between_files_and_sqlite(tmp_path: Path, checkpoint: str) -> None:
    root = tmp_path / "root"
    with Workspace.create(root) as store:
        run_id = prepare(store)
        store.start_run(run_id, 123)
    armed = True

    def fail(point: Literal["before_publish", "after_publish", "before_database_commit"]) -> None:
        if armed and point == checkpoint:
            raise RuntimeError("injected crash boundary")

    # Opening first recovers the pending run, so create a fresh attempt from the immutable draft.
    with Workspace.open(root, fault_hook=fail) as store:
        armed = False
        run = store.prepare_run("document")
        store.start_run(run.run_id, 123)
        armed = True
        with pytest.raises(RuntimeError, match="injected"):
            store.commit_result(run.run_id, receipt(run.run_id), b'{"signal":10}')
        assert store.get_run(run.run_id).state == "committing"
    with Workspace.open(root) as store:
        assert store.get_run(run.run_id).state == "interrupted"
        if checkpoint == "before_publish":
            assert store.recovery.quarantined_paths and not store.recovery.orphan_paths
        else:
            assert "results/" + run.run_id in store.recovery.orphan_paths


def test_cancel_at_publish_cannot_be_overwritten(tmp_path: Path) -> None:
    run_id = ""
    armed = False
    store: Workspace

    def cancel(point: Literal["before_publish", "after_publish", "before_database_commit"]) -> None:
        if armed and point == "after_publish":
            store.request_cancel(run_id)

    with Workspace.create(tmp_path / "root", fault_hook=cancel) as store:
        run_id = prepare(store)
        store.start_run(run_id, 123)
        armed = True
        with pytest.raises(StateConflict):
            store.commit_result(run_id, receipt(run_id), b'{"signal":10}')
        assert store.get_run(run_id).state == "cancelling"
        assert store.finish_cancelled(run_id, receipt(run_id)).state == "cancelled"


@pytest.mark.parametrize(
    "checkpoint", ["before_publish", "after_publish", "before_database_commit"]
)
def test_real_host_crash_releases_lock_and_preserves_history(
    tmp_path: Path, checkpoint: str
) -> None:
    root = tmp_path / "crash-workspace"
    identity_file = tmp_path / "crash-run.txt"
    with Workspace.create(root) as store:
        previous = prepare(store)
        store.start_run(previous, 123)
        completed = store.commit_result(previous, receipt(previous), b'{"signal":10}')
    script = """
import os, sys, subprocess
from pathlib import Path
from platform_runtime.api import Workspace
from tool_contracts.api import ProcessExitReceipt
armed = False
def crash(point):
    if armed and point == sys.argv[2]:
        os._exit(77)
with Workspace.open(sys.argv[1], fault_hook=crash) as store:
    run = store.prepare_run('document')
    child = subprocess.Popen([sys.executable, '-c', 'pass'])
    store.start_run(run.run_id, child.pid)
    code = child.wait(timeout=10)
    Path(sys.argv[3]).write_text(run.run_id, encoding='ascii')
    armed = True
    store.commit_result(run.run_id,
        ProcessExitReceipt(run_id=run.run_id, pid=child.pid, exit_code=code), b'{}')
"""
    crashed = subprocess.run(
        [sys.executable, "-c", script, str(root), checkpoint, str(identity_file)],
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert crashed.returncode == 77, crashed.stderr
    run_id = identity_file.read_text(encoding="ascii")
    with Workspace.open(root) as store:
        assert run_id in store.recovery.interrupted_run_ids
        assert store.get_run(run_id).state == "interrupted"
        assert store.get_run(previous) == completed
        assert store.recovery.quarantined_paths or store.recovery.orphan_paths


@pytest.mark.parametrize(
    "checkpoint", ["before_publish", "after_publish", "before_database_commit"]
)
def test_same_size_corruption_at_commit_is_rejected(tmp_path: Path, checkpoint: str) -> None:
    armed = False
    run_id = ""
    root = tmp_path / "root"

    def corrupt(
        point: Literal["before_publish", "after_publish", "before_database_commit"],
    ) -> None:
        if armed and point == checkpoint:
            if point == "before_publish":
                paths = list((root / ".staging").glob("*/result.json"))
                assert len(paths) == 1
                target = paths[0]
            else:
                target = root / "results" / run_id / "result.json"
            target.write_bytes(b'{"signal":99}')

    with Workspace.create(root, fault_hook=corrupt) as store:
        run_id = prepare(store)
        store.start_run(run_id, 123)
        armed = True
        with pytest.raises(IntegrityError):
            store.commit_result(run_id, receipt(run_id), b'{"signal":10}')
        assert store.get_run(run_id).state == "committing"
    with Workspace.open(root) as store:
        assert store.get_run(run_id).state == "interrupted"
        assert store.recovery.quarantined_paths or store.recovery.orphan_paths


@pytest.mark.parametrize(
    "path",
    ["../outside", "/absolute", "a/../b", "a\\b", "a:b", "a//b", "a/CON.txt", "a.", "a\x00b"],
)
def test_path_contract_rejects_aliases(path: str) -> None:
    with pytest.raises(ValidationError):
        AssetRef(asset_id="a", relative_path=path, sha256="0" * 64, size_bytes=0)


def test_external_hardlink_and_tampered_payload_rejected(
    workspace: Workspace, tmp_path: Path
) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"payload")
    ref = workspace.import_asset(source, sha256(b"payload").hexdigest())
    path = workspace.asset_path(ref)
    external_alias = tmp_path / "alias.bin"
    os.link(path, external_alias)
    with pytest.raises(IntegrityError, match="硬链接"):
        workspace.read_asset(ref)
    external_alias.unlink()
    path.write_bytes(b"changed")
    with pytest.raises(IntegrityError, match="摘要"):
        workspace.read_asset(ref)


def test_real_junction_or_symlink_rejected(workspace: Workspace, tmp_path: Path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"payload")
    ref = workspace.import_asset(source, sha256(b"payload").hexdigest())
    original = workspace.asset_path(ref).parent
    outside = tmp_path / "outside"
    assert original.resolve().is_relative_to(tmp_path.resolve())
    assert outside.resolve().is_relative_to(tmp_path.resolve())
    original.rename(outside)
    if os.name == "nt":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(original), str(outside)],
            cwd=tmp_path,
            capture_output=True,
            check=True,
        )
    else:
        original.symlink_to(outside, target_is_directory=True)
    with pytest.raises(IntegrityError, match="重解析点"):
        workspace.read_asset(ref)


@pytest.mark.parametrize("data", [b'{"x":NaN}', b'{"x":1e999}', b'{"x":1,"x":2}', b"[]"])
def test_invalid_opaque_json_rejected(workspace: Workspace, data: bytes) -> None:
    with pytest.raises(WorkspaceError):
        workspace.save_draft("D", "wb", 0, data, expected_previous_revision=None)
    assert workspace.list_documents() == ()


def test_contract_schema_snapshot() -> None:
    root = Path(__file__).resolve().parents[1]
    assert (
        json.loads((root / "docs/contracts/storage-v1.schema.json").read_text(encoding="utf-8"))
        == storage_contract_schema()
    )


def test_consistent_backup_restores_without_overwriting_source(
    workspace: Workspace, tmp_path: Path
) -> None:
    run_id = prepare(workspace)
    workspace.start_run(run_id, 123)
    done = workspace.commit_result(run_id, receipt(run_id), b'{"signal":10}')
    target = workspace.backup(tmp_path / "备份")
    with Workspace.open(target) as restored:
        assert restored.get_run(run_id) == done
        assert restored.load_draft("document").revision == 0
        assert done.result is not None and restored.read_asset(done.result) == b'{"signal":10}'
    with pytest.raises(WorkspaceError):
        workspace.backup(target)
    with pytest.raises(WorkspaceError):
        workspace.backup(workspace.root / "recursive")
    assert workspace.get_run(run_id) == done


def test_tampered_success_is_not_reported_as_verified(workspace: Workspace) -> None:
    run_id = prepare(workspace)
    workspace.start_run(run_id, 123)
    completed = workspace.commit_result(run_id, receipt(run_id), b'{"signal":10}')
    assert completed.result is not None
    path = workspace.asset_path(completed.result)
    path.write_bytes(b'{"signal":99}')
    with pytest.raises(IntegrityError):
        workspace.get_run(run_id)


def test_wrong_input_digest_is_quarantined_on_reopen(tmp_path: Path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"source")
    root = tmp_path / "root"
    with Workspace.create(root) as store, pytest.raises(IntegrityError):
        store.import_asset(source, "0" * 64)
    with Workspace.open(root) as store:
        assert store.recovery.quarantined_paths
        assert source.read_bytes() == b"source"


def test_real_worker_snapshot_to_published_result(workspace: Workspace, tmp_path: Path) -> None:
    original = tmp_path / "real.tif"
    tifffile.imwrite(original, np.array([[245], [235], [245]], dtype=np.uint8))
    image = load_tiff(original)
    asset = workspace.import_asset(original, image.sha256)
    request = AnalysisRequest(
        image.sha256,
        0,
        "dark",
        (LaneAnnotation(LaneROI("L", 0, 0, 1, 3), (BandAnnotation("B", BandBounds(0, 2)),)),),
    )
    start = StartFrame(
        protocol_version=1,
        kind="start",
        sequence=0,
        run_id="draft",
        attempt_id="draft",
        request_id="draft",
        source_path=asset.relative_path,
        request=request,
    )
    workspace.save_draft(
        "D", "wb", 0, encode_worker_frame(start).strip(), expected_previous_revision=None
    )
    run = workspace.prepare_run("D")
    workspace.save_draft("D", "wb", 1, b'{"new_draft":true}', expected_previous_revision=0)
    start = start.model_copy(
        update={"run_id": run.run_id, "source_path": str(workspace.asset_path(asset))}
    )
    original.write_bytes(b"source edited by test after snapshot")
    process = subprocess.Popen(
        [sys.executable, "-m", "wb_tool.worker"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=tmp_path,
    )
    workspace.start_run(run.run_id, process.pid)
    stdout, stderr = process.communicate(encode_worker_frame(start), timeout=30)
    assert process.returncode == 0, stderr
    conversation = WorkerConversation(start)
    received = [conversation.accept(data) for data in stdout.splitlines()]
    assert isinstance(received[-1], ResultFrame)
    assert received[-1].result.lanes[0].bands[0].signal == 10
    completed = workspace.commit_result(
        run.run_id,
        ProcessExitReceipt(run_id=run.run_id, pid=process.pid, exit_code=process.returncode),
        encode_worker_frame(received[-1]).strip(),
    )
    assert completed.state == "succeeded" and completed.revision == 0
    assert workspace.load_draft("D").revision == 1
    assert completed.result is not None
    assert json.loads(workspace.read_asset(completed.result))["result"]["request"]["revision"] == 0
