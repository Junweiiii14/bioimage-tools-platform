"""Retained controls belong to the view, including hidden compatibility controls."""

import json
import subprocess
import sys


def test_destroying_figure_view_parent_destroys_its_hidden_controls() -> None:
    # Observe the real process exit as well as QObject destruction, without
    # destroying objects or flushing deferred deletions in pytest's Qt session.
    script = """
import json
import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QWidget
from wb_tool.api import create_figure_project_view
app = QApplication([])
parent = QWidget()
view = create_figure_project_view(parent)
assert view.parent() is parent
created = app.topLevelWidgets()
assert created
parent.deleteLater()
QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
assert not shiboken6.isValid(parent) and not shiboken6.isValid(view)
survivors = [type(widget).__name__ for widget in created if shiboken6.isValid(widget)]
print(json.dumps(survivors))
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-c", script], capture_output=True, text=True, timeout=20
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == []
