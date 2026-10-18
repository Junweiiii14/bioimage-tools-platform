"""Diagnostic inventory is bounded and never exposes widget content."""

import json
from typing import Protocol, cast

import pytest
from PySide6.QtWidgets import QLineEdit, QWidget
from pytestqt.qtbot import QtBot

from tooling import qt_exit_inventory
from tooling.qt_exit_inventory import remember_roots, snapshot


class RequestNode(Protocol):
    @property
    def node(self) -> pytest.Item: ...


def test_inventory_records_live_structure_without_reading_widget_text(qtbot: QtBot) -> None:
    root = QWidget()
    qtbot.addWidget(root)
    secret = "must-not-appear-in-diagnostics"
    root.setObjectName(secret)
    root.setWindowTitle(secret)
    child = QLineEdit(root)
    child.setText(secret)
    remember_roots("controlled_test")
    report = snapshot()
    encoded = json.dumps(report)
    assert secret not in encoded
    assert hex(id(root)) in encoded and hex(id(child)) in encoded
    assert "controlled_test" in encoded
    assert root.children() and child.text() == secret


def test_inventory_budget_is_enforced(qtbot: QtBot) -> None:
    root = QWidget()
    qtbot.addWidget(root)
    QLineEdit(root)
    report = snapshot(max_nodes=1)
    assert report["truncated"] is True
    objects = report["objects"]
    assert isinstance(objects, list) and len(cast(list[object], objects)) == 1
    with pytest.raises(ValueError):
        snapshot(max_nodes=True)


def test_teardown_observation_failure_is_reported_without_raising(
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    request: pytest.FixtureRequest,
) -> None:
    def unavailable():
        raise ValueError("controlled-private-context-must-not-be-logged")

    with monkeypatch.context() as patch:
        patch.setattr(qt_exit_inventory, "_roots", unavailable)
        qt_exit_inventory.pytest_runtest_teardown(cast(RequestNode, request).node)
    message = capsys.readouterr().err
    assert "QT_EXIT_INVENTORY_UNAVAILABLE" in message and "ValueError" in message
    assert "controlled-private-context" not in message
