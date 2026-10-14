"""Actual child processes prove fatal diagnostics survive abort without affecting worker stdout."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = r"""
import os, sys, faulthandler
from pathlib import Path
from PySide6.QtCore import QCoreApplication, qWarning, qFatal, qInstallMessageHandler
from bioimage_app.api import DesktopDiagnostics
if os.name == 'nt':
    import ctypes
    ctypes.windll.kernel32.SetErrorMode(0x0001 | 0x0002)
app = QCoreApplication([])
received = []
qInstallMessageHandler(lambda level, context, message: received.append(message))
original_hook = sys.excepthook
original_fatal = faulthandler.is_enabled()
diagnostics = DesktopDiagnostics(Path(sys.argv[1]))
qWarning('diagnostic-probe')
assert received == ['diagnostic-probe']
if sys.argv[2] == 'fatal':
    qFatal('intentional-diagnostic-abort')
elif sys.argv[2] == 'exception':
    try:
        raise ValueError('diagnostic-python-exception')
    except ValueError:
        sys.excepthook(*sys.exc_info())
diagnostics.close()
diagnostics.close()
assert sys.excepthook is original_hook
assert faulthandler.is_enabled() is original_fatal
qWarning('after-close')
assert received[-1] == 'after-close'
print('diagnostics-closed')
"""


@pytest.mark.parametrize("mode", ["normal", "exception", "fatal"])
def test_real_diagnostic_process(tmp_path: Path, mode: str) -> None:
    environment = dict(os.environ)
    environment.pop("PYTHONFAULTHANDLER", None)
    child = subprocess.run(
        [sys.executable, "-I", "-c", SCRIPT, str(tmp_path), mode],
        capture_output=True,
        timeout=15,
        env=environment,
    )
    logs = list(tmp_path.glob("session-*.log"))
    assert len(logs) == 1
    text = logs[0].read_text(encoding="utf-8")
    rows = [json.loads(line) for line in text.splitlines() if line.startswith("{")]
    assert any(
        row["kind"] == "QtWarningMsg" and row["message"] == "diagnostic-probe" for row in rows
    )
    if mode == "fatal":
        assert child.returncode != 0
        assert "intentional-diagnostic-abort" in text
        assert "Current thread" in text and "_qt_message" in text
        assert "session_end" not in text
    else:
        assert child.returncode == 0, child.stderr
        assert child.stdout.strip() == b"diagnostics-closed"
        assert rows[-1]["kind"] == "session_end"
        assert "after-close" not in text
        if mode == "exception":
            assert "diagnostic-python-exception" in text and "ValueError" in text
