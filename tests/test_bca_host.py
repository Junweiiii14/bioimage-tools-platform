"""Real worker/commit/reopen, failure and cancellation on the existing host."""

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from bioimage_app.bca_cli import prepare
from bioimage_app.bca_workflow_host import BcaHost
from bioimage_app.workflow_session import WorkflowSession, WorkflowStatus
from platform_runtime.api import WorkspaceError
from pytestqt.qtbot import QtBot

EXAMPLES = Path(__file__).parents[1] / "tools/bca/examples"


def cli(workspace: Path, *arguments: str) -> tuple[int, dict[str, Any]]:
    process = subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "bioimage_app.bca_cli",
            "--workspace",
            str(workspace),
            *arguments,
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    lines = process.stdout.splitlines()
    return process.returncode, json.loads(lines[-1]) if lines else {"error": process.stderr}


def test_real_csv_worker_commit_reopen_and_protection(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    source, record = EXAMPLES / "synthetic.csv", EXAMPLES / "record.json"
    original = source.read_bytes()
    code, finished = cli(workspace, "--source", str(source), "--record", str(record))
    assert code == 0, finished
    assert finished["state"] == "succeeded"
    paths = {k: Path(v) for k, v in finished["outputs"].items()}
    saved = {k: p.read_bytes() for k, p in paths.items()}
    samples = list(csv.DictReader(paths["samples"].open(encoding="utf-8")))
    assert float(samples[0]["mean_original_ug_ml"]) == pytest.approx(5008.680555555556, abs=1e-10)
    assert samples[-1]["mean_original_ug_ml"] == ""
    assert samples[-1]["n_valid"] == "1"
    provenance = json.loads(saved["provenance"])
    assert provenance["record"]["source_sha256"] == hashlib.sha256(original).hexdigest()
    assert provenance["record_sha256"] == hashlib.sha256(record.read_bytes()).hexdigest()
    assert provenance["loq"] is None
    code, reopened = cli(workspace, "--reopen", finished["execution_id"])
    assert code == 0 and reopened["outputs"] == finished["outputs"], reopened
    assert reopened["pid"] is None
    with pytest.raises(WorkspaceError):
        prepare(workspace, str(source), str(record), BcaHost())
    assert {k: p.read_bytes() for k, p in paths.items()} == saved
    assert source.read_bytes() == original


def test_worker_curve_failure_has_no_results(tmp_path: Path) -> None:
    source, record = tmp_path / "bad.csv", tmp_path / "record.json"
    rows = list(csv.DictReader((EXAMPLES / "synthetic.csv").open(encoding="utf-8")))
    rows[2]["a562"] = "3"
    with source.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    metadata = json.loads((EXAMPLES / "record.json").read_text())
    metadata["source_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    record.write_text(json.dumps(metadata))
    code, result = cli(tmp_path / "workspace", "--source", str(source), "--record", str(record))
    assert code != 0 and result["state"] == "failed", result
    assert "invalid_curve" in result["failure_reason"] and result["outputs"] == {}


def test_active_worker_cancel_publishes_no_result(tmp_path: Path, qtbot: QtBot) -> None:
    workspace = tmp_path / "workspace"
    host = BcaHost()
    plan = prepare(workspace, str(EXAMPLES / "synthetic.csv"), str(EXAMPLES / "record.json"), host)
    session = WorkflowSession(host.registry)
    observed_pids: list[int] = []

    def changed(status: WorkflowStatus) -> None:
        if status.pid is not None and not observed_pids:
            observed_pids.append(status.pid)
            session.cancel()

    session.changed.connect(changed)

    def completed(_status: WorkflowStatus) -> None:
        session.close()

    session.completed.connect(completed)
    with qtbot.waitSignal(session.finished, timeout=20000):
        session.start(str(workspace), plan)
    assert observed_pids
    assert session.ledger is not None
    assert session.ledger.state == "cancelled" and session.ledger.results == ()
