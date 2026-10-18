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


@pytest.fixture
def controlled_roots(monkeypatch: pytest.MonkeyPatch) -> list[QWidget]:
    # Unit observations must not depend on unrelated product windows or Qt's
    # global root ordering. The plugin's real teardown observes globals again.
    roots: list[QWidget] = []
    monkeypatch.setattr(qt_exit_inventory, "_roots", lambda: roots)
    monkeypatch.setattr(qt_exit_inventory, "_origins", {})
    return roots


def test_inventory_records_live_structure_without_reading_widget_text(
    qtbot: QtBot, controlled_roots: list[QWidget]
) -> None:
    root = QWidget()
    qtbot.addWidget(root)
    controlled_roots.append(root)
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


def test_inventory_budget_is_enforced(qtbot: QtBot, controlled_roots: list[QWidget]) -> None:
    root = QWidget()
    qtbot.addWidget(root)
    other = QWidget()
    qtbot.addWidget(other)
    controlled_roots.extend((root, other))
    QLineEdit(root)
    report = snapshot(max_nodes=1)
    assert report["truncated"] is True
    assert report["root_count"] == 2
    objects = report["objects"]
    assert isinstance(objects, list) and len(cast(list[object], objects)) == 1
    with pytest.raises(ValueError):
        snapshot(max_nodes=True)


def test_root_budget_reports_omitted_roots(qtbot: QtBot, controlled_roots: list[QWidget]) -> None:
    for _ in range(129):
        root = QWidget()
        qtbot.addWidget(root)
        controlled_roots.append(root)
    remember_roots("controlled_roots")
    report = snapshot(max_nodes=512)
    assert report["root_count"] == 129 and report["truncated"] is True
    records = cast(list[dict[str, object]], report["objects"])
    assert len(records) == 128
    assert {record["python_id"] for record in records} == {
        hex(id(root)) for root in controlled_roots[:128]
    }
    assert hex(id(controlled_roots[-1])) not in json.dumps(report)


def test_origin_capacity_is_bounded_and_missing_origin_is_explicit(
    qtbot: QtBot, controlled_roots: list[QWidget], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(qt_exit_inventory, "_MAX_ORIGINS", 2)
    for _ in range(3):
        root = QWidget()
        qtbot.addWidget(root)
        controlled_roots.append(root)
    remember_roots("controlled_origin")
    report = snapshot()
    assert report["origin_capacity_reached"] is True
    records = cast(list[dict[str, object]], report["objects"])
    assert [record["first_observed_after"] for record in records] == [
        "controlled_origin",
        "controlled_origin",
        "unattributed",
    ]


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
