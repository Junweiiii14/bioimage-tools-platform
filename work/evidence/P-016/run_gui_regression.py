"""Real Qt controller/model regression. Native chooser is substituted; model is not.
The independent first-gui-run.json records the actual native-click happy path.
"""

import hashlib
import json
import time
from pathlib import Path
from unittest.mock import patch

import numpy as np
from bioimage_app.nuclei_bridge import NucleiBridge
from bioimage_app.nuclei_results import read_result
from PIL import Image
from platform_runtime.api import Workspace
from PySide6.QtCore import QEventLoop, QSettings, QTimer
from PySide6.QtWidgets import QApplication, QFileDialog, QWidget

root = Path("C:/Users/70236/ResearchVault/Codex-Workbench/p016-research/regression-01")
root.mkdir(parents=True, exist_ok=False)
app = QApplication([])
window = QWidget()
settings = QSettings(str(root / "settings.ini"), QSettings.Format.IniFormat)
settings.setValue(
    "nuclei_worker_v1",
    "C:/Users/70236/ResearchVault/Codex-Workbench/p015-research/worker-env/Scripts/python.exe",
)
model = "C:/Users/70236/ResearchVault/Codex-Workbench/p014-research/models/2D_versatile_fluo"
settings.setValue("nuclei_model_v1", model)
bridge = NucleiBridge(window, settings, lambda: False)
states = []
bridge.changed.connect(lambda raw: states.append(json.loads(raw)))
gaps = []
last = time.monotonic()


def beat():
    global last
    now = time.monotonic()
    gaps.append(now - last)
    last = now


heartbeat = QTimer()
heartbeat.timeout.connect(beat)
heartbeat.start(20)


def wait_idle():
    if not bridge.busy:
        return
    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    bridge.idle.connect(loop.quit)
    timer.start(30000)
    loop.exec()
    bridge.idle.disconnect(loop.quit)
    timer.stop()
    assert not bridge.busy, "GUI operation did not become idle within 30 seconds"


def choose(path):
    with patch.object(QFileDialog, "getOpenFileName", return_value=(str(path), "TIFF")):
        bridge.choose("source")
    wait_idle()


source = root / "zero.tif"
Image.fromarray(np.zeros((128, 192), dtype=np.uint8)).save(source)
before = hashlib.sha256(source.read_bytes()).hexdigest()
choose(source)
bridge.run()
wait_idle()
zero = states[-1]
assert zero["state"] == "succeeded" and zero["count"] == 0
zero_result = read_result(zero["workspace"])
zero_labels = hashlib.sha256(zero_result.labels).hexdigest()
assert (
    np.count_nonzero(np.load(__import__("io").BytesIO(zero_result.labels), allow_pickle=False)) == 0
)
bad = root / "16bit.tif"
Image.fromarray(np.zeros((128, 192), dtype=np.uint16)).save(bad)
choose(bad)
assert states[-1]["state"] == "failed" and states[-1]["run_id"] == zero["run_id"]
unsupported_preserved = states[-1]["run_id"]
choose(source)
settings.setValue("nuclei_model_v1", str(root / "missing-model"))
bridge.run()
wait_idle()
missing = states[-1]
assert missing["state"] == "failed" and missing["count"] is None
assert not Path(missing["workspace"]).exists()
settings.setValue("nuclei_model_v1", model)
choose(source)
cancel_pid = []
poll = QTimer()


def cancel_running():
    session = bridge._session
    if session is not None and session.status().pid:
        cancel_pid.append(session.status().pid)
        poll.stop()
        bridge.cancel()


poll.timeout.connect(cancel_running)
bridge.run()
poll.start(20)
wait_idle()
poll.stop()
cancelled = states[-1]
assert cancel_pid and cancelled["state"] == "cancelled" and cancelled["count"] is None
with Workspace.open(cancelled["workspace"]) as store:
    assert all(run.state != "succeeded" and run.result is None for run in store.list_runs())
assert hashlib.sha256(read_result(zero["workspace"]).labels).hexdigest() == zero_labels
assert hashlib.sha256(source.read_bytes()).hexdigest() == before
bridge.close()
assert bridge.resources_closed
heartbeat.stop()
report = dict(
    zero={k: zero[k] for k in ("state", "count", "run_id", "workspace")},
    unsupported_previous_run_preserved=unsupported_preserved,
    missing_model={k: missing[k] for k in ("state", "count", "message")},
    cancelled={k: cancelled[k] for k in ("state", "count", "workspace")},
    cancel_observed_pid=cancel_pid[0],
    original_unchanged=True,
    old_labels_unchanged=True,
    heartbeat_samples=len(gaps),
    max_heartbeat_gap_seconds=max(gaps),
    note=(
        "Qt controller actual model; native dialogs substituted. Not student/scientific acceptance."
    ),
)
(root / "report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
Path("work/evidence/P-016/gui-regression.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(report, ensure_ascii=False))
