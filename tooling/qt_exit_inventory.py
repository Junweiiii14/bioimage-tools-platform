"""Opt-in, bounded Qt object inventory; no destruction, events or signal callbacks.

Use pytest -p tooling.qt_exit_inventory alongside the native exception observer.
Object wrappers are held only during each observation; origins use weak references.
No widget text, object names, titles, properties or source images are read.
"""

from __future__ import annotations

import json
import os
import sys
import weakref
from collections import deque
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from PySide6.QtCore import QObject
    from PySide6.QtWidgets import QWidget

_MAX_ORIGINS = 1024
_origins: dict[int, tuple[weakref.ReferenceType[QWidget], str]] = {}


def _roots() -> list[QWidget]:
    if "PySide6.QtWidgets" not in sys.modules:
        return []
    from PySide6.QtWidgets import QApplication

    if not isinstance(QApplication.instance(), QApplication):
        return []
    return QApplication.topLevelWidgets()


def remember_roots(label: str) -> None:
    """Remember first observation, without extending a widget's lifetime."""
    roots = _roots()
    for widget in roots[:128]:
        key = id(widget)
        previous = _origins.get(key)
        if previous is not None and previous[0]() is widget:
            continue
        if len(_origins) >= _MAX_ORIGINS:
            dead = [key for key, (reference, _) in _origins.items() if reference() is None]
            for dead_key in dead:
                del _origins[dead_key]
        if len(_origins) < _MAX_ORIGINS:
            _origins[key] = (weakref.ref(widget), label[:240])


def snapshot(*, max_nodes: int = 256) -> dict[str, object]:
    """Describe live roots/parents/children with fixed budgets and no cleanup."""
    if type(max_nodes) is not int or not 1 <= max_nodes <= 512:
        raise ValueError("Qt inventory budget must be 1–512 objects")
    roots = _roots()
    records: list[dict[str, object]] = []
    truncated = len(roots) > 128
    if not roots:
        return {"schema": 1, "root_count": 0, "objects": records, "truncated": False}
    import shiboken6

    queue: deque[tuple[QObject, str]] = deque()
    for widget in roots[:128]:
        entry = _origins.get(id(widget))
        origin = entry[1] if entry and entry[0]() is widget else "unattributed"
        queue.append((widget, origin))
    visited: set[int] = set()
    while queue and len(records) < max_nodes:
        obj, origin = queue.popleft()
        if id(obj) in visited or not shiboken6.isValid(obj):
            continue
        visited.add(id(obj))
        parent = obj.parent()
        pointers = shiboken6.getCppPointer(obj)
        records.append(
            {
                "python_id": hex(id(obj)),
                "cpp_id": hex(pointers[0]) if pointers else None,
                "type": type(obj).__module__ + "." + type(obj).__qualname__,
                "parent_python_id": hex(id(parent)) if parent is not None else None,
                "first_observed_after": origin,
            }
        )
        # children() creates temporary wrappers; this is observation, not a proof
        # that instrumenting the process cannot affect finalization timing.
        children = obj.children()
        remaining = max_nodes - len(records) - len(queue)
        truncated |= len(children) > max(0, remaining)
        queue.extend((child, origin) for child in children[: max(0, remaining)])
    return {
        "schema": 1,
        "root_count": len(roots),
        "objects": records,
        "truncated": truncated or bool(queue),
        "origin_capacity_reached": len(_origins) >= _MAX_ORIGINS,
    }


@pytest.hookimpl(trylast=True)
def pytest_runtest_teardown(item: pytest.Item) -> None:
    if isinstance(item, pytest.Function) and (
        "qtbot" in item.fixturenames or "qapp" in item.fixturenames
    ):
        # Omit parametrized values; only repository test location/function names.
        remember_roots(item.nodeid.split("[", 1)[0])


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(exitstatus: int) -> None:
    try:
        report = snapshot()
    except Exception as error:
        report = {"schema": 1, "unavailable": type(error).__name__}
    report.update(phase="pytest_sessionfinish", pid=os.getpid(), pytest_exitstatus=int(exitstatus))
    print("QT_EXIT_INVENTORY " + json.dumps(report, ensure_ascii=True), file=sys.stderr, flush=True)
