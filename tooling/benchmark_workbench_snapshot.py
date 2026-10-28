"""Opt-in synthetic WorkbenchBridge benchmark; never a CI gate or scientific acceptance."""

import argparse
import ctypes
import hashlib
import json
import math
import os
import platform
import random
import re
import statistics
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from contextlib import nullcontext
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, cast
from unittest.mock import patch

from tool_contracts.api import AssetRef
from wb_tool.api import (
    FigureRow,
    IntakeAssignment,
    IntakeFigure,
    IntakeManifest,
    IntakeProtein,
    IntakeSource,
    PreviewRaster,
    ProjectTableCell,
    WBFigureProject,
    WBIntakeProject,
)

if TYPE_CHECKING:
    from bioimage_app.web_window import WebWorkbenchWindow
    from pytestqt.qtbot import QtBot

ROOT = Path(__file__).resolve().parents[1]
BUDGETS = {
    "snapshot_and_json_p95_ms": 50,
    "refresh_click_p95_ms": 200,
    "idle_publish_p95_ms": 1,
    "idle_snapshot_calls": 0,
    "idle_state_emissions": 0,
    "snapshot_utf8_bytes": 16 * 1024**2,
    "host_renderer_private_bytes": 2 * 1024**3,
}


@dataclass(frozen=True)
class Scenario:
    name: str
    intake: bool
    rows: int
    figures: int
    lanes: int


SCENARIOS = {
    item.name: item
    for item in (
        Scenario("rows-small", False, 4, 2, 6),
        Scenario("rows-limit", False, 512, 128, 96),
        Scenario("intake-small", True, 4, 2, 6),
        Scenario("intake-limit", True, 512, 128, 96),
    )
}


def fixture(case: Scenario) -> tuple[WBFigureProject, tuple[PreviewRaster, ...]]:
    """Synthetic validated identities/display rasters; never read or publish original assets."""
    if not 1 <= case.rows <= 512 or not 1 <= case.lanes <= 96:
        raise ValueError("Fixture exceeds the existing row/lane contract")
    if not 1 <= case.figures <= case.rows or case.rows % case.figures:
        raise ValueError("Fixture figures must evenly partition rows")
    rows: list[FigureRow] = []
    sources: list[IntakeSource] = []
    rasters: list[PreviewRaster] = []
    rng = random.Random(8209)
    for index in range(case.rows):
        # Incompressible deterministic display-only pixels exercise inline PNG size.
        pixels = rng.randbytes(128 * 128)
        digest = hashlib.sha256(pixels).hexdigest()
        asset = AssetRef(
            asset_id=f"synthetic-{index}",
            relative_path=f"assets/{index}.tif",
            sha256=digest,
            size_bytes=1024 * 512 * 2,
        )
        figure = index // (case.rows // case.figures)
        rows.append(
            FigureRow(
                row_id=f"row-{index}",
                source=asset,
                filename=f"synthetic-{index}.tif",
                width=1024,
                height=512,
                bit_depth=16,
                figure=f"Fig{figure + 1}",
                protein=f"Protein{index}",
                lane_count=case.lanes,
                notes="Synthetic metadata only; no measured result or original asset exists.",
            )
        )
        sources.append(
            IntakeSource(
                source_id=f"source-{index}",
                asset=asset,
                original_name=f"synthetic-{index}.tif",
                relative_path=f"synthetic-{index}.tif",
                width=1024,
                height=512,
                bit_depth=16,
            )
        )
        rasters.append(PreviewRaster(digest, 1024, 512, 128, 128, pixels, 16, ()))
    fields: dict[str, object] = {
        "project_id": "synthetic-r09-" + case.name,
        "name": "R09 synthetic " + case.name,
        "rows": tuple(rows),
        "figure_order": tuple(f"Fig{i + 1}" for i in range(case.figures)),
    }
    if case.intake:
        # Intake validates this projection against its own manifest; no model_construct bypass.
        fields["intake"] = IntakeManifest(
            figures=tuple(
                IntakeFigure(figure_id=f"fig-{i}", label=f"Fig{i + 1}", lane_count=case.lanes)
                for i in range(case.figures)
            ),
            proteins=tuple(
                IntakeProtein(
                    protein_id=row.row_id,
                    figure_id=f"fig-{i // (case.rows // case.figures)}",
                    label=row.protein,
                )
                for i, row in enumerate(rows)
            ),
            sources=tuple(sources),
            assignments=tuple(
                IntakeAssignment(protein_id=row.row_id, source_id=f"source-{i}")
                for i, row in enumerate(rows)
            ),
        )
        # The intake projection has empty notes; retain exactly its public contract.
        fields["rows"] = tuple(row.model_copy(update={"notes": ""}) for row in rows)
        project = WBIntakeProject.model_validate(fields)
    else:
        project = WBFigureProject.model_validate(fields)
    return project, tuple(rasters)


def cells(project: WBFigureProject) -> tuple[ProjectTableCell, ...]:
    return tuple(
        ProjectTableCell(
            row_id=row.row_id,
            figure=row.figure,
            protein=row.protein,
            lane_index=lane,
            source_sha256=row.source.sha256 if row.source else "",
            lane_id=f"{row.row_id}-{lane}",
            band_id="",
            request_revision=None,
            run_id="",
            value=None,
            status="pending_review",
            reason="Synthetic pending row; no measurement performed",
        )
        for row in project.rows
        for lane in range(1, row.lane_count + 1)
    )


def distribution(values: list[float]) -> dict[str, object]:
    if not values or any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("Samples must be nonempty, finite and nonnegative")
    ordered = sorted(values)
    return {
        "n": len(values),
        "p50": statistics.median(values),
        "p95": ordered[math.ceil(0.95 * len(values)) - 1],
        "max": max(values),
        "samples": values,
        "quantile": "nearest-rank ceil(0.95*n), no interpolation",
    }


def windows_memory(pid: int) -> dict[str, int]:
    """PSAPI per-process private commitment and working set; not a process-tree total."""
    if sys.platform != "win32":
        raise RuntimeError("The native benchmark currently measures Windows only")

    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("faults", ctypes.c_ulong)] + [
            (name, ctypes.c_size_t)
            for name in (
                "peak_working_set",
                "working_set",
                "peak_paged",
                "paged",
                "peak_nonpaged",
                "nonpaged",
                "pagefile",
                "peak_pagefile",
                "private",
            )
        ]

    kernel: Any = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi: Any = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_bool, ctypes.c_ulong]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    psapi.GetProcessMemoryInfo.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(Counters),
        ctypes.c_ulong,
    ]
    handle = kernel.OpenProcess(0x0400 | 0x0010, False, pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    counter = Counters()
    counter.cb = ctypes.sizeof(counter)
    try:
        if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counter), counter.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return {
            "pid": pid,
            "private_bytes": int(counter.private),
            "working_set_bytes": int(counter.working_set),
            "peak_working_set_bytes": int(counter.peak_working_set),
        }
    finally:
        kernel.CloseHandle(handle)


class EventPump:
    """The waitUntil surface consumed by the existing owned-window cleanup helper."""

    def waitUntil(self, callback: Callable[[], bool], *, timeout: int = 30000) -> None:
        from PySide6.QtTest import QTest

        deadline = time.perf_counter() + timeout / 1000
        while not callback():
            if time.perf_counter() > deadline:
                raise TimeoutError("Benchmark Qt/JavaScript deadline exceeded")
            QTest.qWait(5)


def javascript(window: "WebWorkbenchWindow", pump: EventPump, code: str) -> object:
    reply: list[object] = []
    window.web.page().runJavaScript(code, reply.append)
    pump.waitUntil(lambda: bool(reply))
    return reply[0]


class SnapshotProvider(Protocol):
    def snapshot(self) -> dict[str, object]: ...


def forward_benchmark_request(
    bridge: SnapshotProvider, request: Callable[[str, str], None], action: str, payload: str
) -> None:
    """Stamp only a marked refresh while forwarding the unchanged real request/publish path."""
    nonce: str | None = None
    if action == "refresh" and len(payload) <= 4096:
        try:
            data: object = json.loads(payload)
        except ValueError:
            data = None  # The real request remains responsible for invalid user payloads.
        if isinstance(data, dict):
            value = cast(dict[str, object], data).get("__r09Nonce")
            if isinstance(value, str) and re.fullmatch(r"r09-[a-z0-9-]{1,80}", value):
                nonce = value
    if nonce is None:
        request(action, payload)
        return
    original_snapshot = bridge.snapshot

    def snapshot_with_nonce() -> dict[str, object]:
        return original_snapshot() | {"__r09Nonce": nonce}

    with patch.object(bridge, "snapshot", snapshot_with_nonce):
        request(action, payload)


CLICK_DRIVER = r"""
(() => {
  const button = document.createElement('button');
  button.id = 'r09-refresh'; button.textContent = 'R09 refresh probe';
  button.style.cssText = 'position:fixed;left:8px;top:8px;z-index:2147483647;' +
    'width:180px;height:40px';
  document.body.append(button);
  window.r09 = {pending:false, samples:[], handlerSamples:[], trusted:[], errors:[],
    project:state.projectId, renderSequence:0, renderedNonce:null, paintNonce:null};
  const fail = message => { r09.errors.push(message); r09.pending = false; };
  const originalReport = boundaryDiagnostics.report;
  boundaryDiagnostics.report = function(...args) {
    fail('Production boundary failure: ' + args[0]);
    return originalReport(...args);
  };
  const originalRender = render;
  render = function(...args) {
    const result = originalRender.apply(this, args);
    // An exception cannot increment this sequence or acknowledge a rendered nonce.
    r09.renderSequence++;
    r09.renderedNonce = state.__r09Nonce;
    return result;
  };
  bridge.stateChanged.connect(raw => {
    if (!r09.pending) return;
    const next = JSON.parse(raw);
    const nonce = r09.nonce;
    if (next.__r09Nonce !== nonce || r09.paintNonce === nonce) return;
    if (next.projectId !== r09.project || state.projectId !== next.projectId ||
        state.revision !== next.revision || state.rows.length !== next.rows.length ||
        state.__r09Nonce !== nonce || r09.renderedNonce !== nonce ||
        r09.renderSequence <= r09.startRenderSequence || r09.errors.length) {
      fail('The production page did not successfully render this click receipt'); return;
    }
    r09.paintNonce = nonce;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      if (!r09.pending || r09.nonce !== nonce) return;
      if (state.__r09Nonce !== nonce || r09.renderedNonce !== nonce || r09.errors.length) {
        fail('The accepted click receipt changed before the paint opportunity'); return;
      }
      r09.samples.push(performance.now() - r09.start);
      r09.handlerSamples.push(performance.now() - r09.handlerStart); r09.pending = false;
    }));
  });
  button.addEventListener('click', event => {
    if (r09.pending) { fail('Overlapping click'); return; }
    if (!event.isTrusted) { fail('Non-native click'); return; }
    r09.trusted.push(event.isTrusted); r09.handlerStart = performance.now();
    r09.start = event.timeStamp; r09.pending = true;
    r09.nonce = 'r09-' + crypto.randomUUID();
    r09.startRenderSequence = r09.renderSequence; r09.paintNonce = null;
    bridge.request('refresh', JSON.stringify({__r09Nonce:r09.nonce}));
  });
  return true;
})()
"""


def measure(case: Scenario, samples: int, warmup: int) -> dict[str, object]:
    from bioimage_app.web_bridge import WorkbenchBridge
    from bioimage_app.web_window import WebWorkbenchWindow
    from PySide6.QtCore import QPoint, QSettings, Qt, Slot, qVersion
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication

    from tooling.qt_test_lifecycle import close_and_dispose_window

    class BenchmarkBridge(WorkbenchBridge):
        @Slot(str, str)
        def request(self, action: str, payload: str = "{}") -> None:
            forward_benchmark_request(self, super().request, action, payload)

    if sys.platform != "win32" or os.environ.get("QT_QPA_PLATFORM", "windows") != "windows":
        raise RuntimeError("Click/paint timings require the visible native Windows Qt platform")
    app = QApplication.instance() or QApplication([])
    if not isinstance(app, QApplication):
        raise RuntimeError("A widget QApplication is required")
    app.setQuitOnLastWindowClosed(False)
    pump = EventPump()
    project, rasters = fixture(case)
    with tempfile.TemporaryDirectory(prefix="bioimage-r09-") as directory:
        # Only this disposable window gets the marked-refresh slot. The timing and idle
        # sections call the inherited original snapshot directly, without a nonce wrapper.
        with patch("bioimage_app.web_window.WorkbenchBridge", BenchmarkBridge):
            window = WebWorkbenchWindow(
                settings=QSettings(
                    str(Path(directory) / "settings.ini"), QSettings.Format.IniFormat
                )
            )
        window.show()
        bridge = window.bridge
        bridge.timer.stop()
        window.session_timer.stop()
        try:
            pump.waitUntil(
                lambda: (
                    javascript(window, pump, "typeof bridge !== 'undefined' && !!bridge") is True
                )
            )
            window.host.view.set_project(project)
            for raster in rasters:
                window.host.view.install_thumbnail(raster)
            window.host.view.analysis.result_view.show_cells(cells(project))
            bridge.request("refresh", "{}")
            pump.waitUntil(
                lambda: javascript(window, pump, "state.projectId") == project.project_id
            )
            javascript(window, pump, "platformHome.show('project');true")
            QTest.qWait(300)
            memory_before = {
                "host": windows_memory(os.getpid()),
                "renderer": windows_memory(window.web.page().renderProcessPid()),
            }
            timings: dict[str, object] = {}
            byte_counts: list[int] = []
            for cache in ("cold_image_cache", "warm_image_cache"):
                construct: list[float] = []
                serialize: list[float] = []
                total: list[float] = []
                for index in range(samples + warmup):
                    # Deliberate benchmark-only cold PNG cache; project/raster caches stay warm.
                    context = (
                        patch.object(bridge, "_images", dict[str, str | None]())
                        if cache == "cold_image_cache"
                        else nullcontext()
                    )
                    with context:
                        start = time.perf_counter_ns()
                        snapshot = bridge.snapshot()
                        middle = time.perf_counter_ns()
                        encoded = json.dumps(snapshot, ensure_ascii=False, allow_nan=False)
                        end = time.perf_counter_ns()
                    if index >= warmup:
                        construct.append((middle - start) / 1e6)
                        serialize.append((end - middle) / 1e6)
                        total.append((end - start) / 1e6)
                        byte_counts.append(len(encoded.encode("utf-8")))
                timings[cache] = {
                    "construct_ms": distribution(construct),
                    "serialize_ms": distribution(serialize),
                    "total_ms": distribution(total),
                }
            bridge.publish()
            emitted: list[str] = []
            bridge.stateChanged.connect(emitted.append)
            idle: list[float] = []
            with patch.object(bridge, "snapshot", wraps=bridge.snapshot) as counted:
                for _ in range(samples):
                    start = time.perf_counter_ns()
                    bridge.publish()
                    idle.append((time.perf_counter_ns() - start) / 1e6)
                idle_calls = counted.call_count
            bridge.stateChanged.disconnect(emitted.append)
            javascript(window, pump, CLICK_DRIVER)
            click_values: list[float] = []
            target = window.web.focusProxy()
            if target is None:
                raise RuntimeError("WebEngine has no native input target")
            for index in range(samples + warmup):
                QTest.mouseClick(
                    target,
                    Qt.MouseButton.LeftButton,
                    Qt.KeyboardModifier.NoModifier,
                    QPoint(80, 25),
                )
                pump.waitUntil(
                    lambda index=index: (
                        javascript(
                            window, pump, f"r09.samples.length > {index} || r09.errors.length > 0"
                        )
                        is True
                    )
                )
                errors = javascript(window, pump, "JSON.stringify(r09.errors)")
                if errors != "[]":
                    raise RuntimeError(f"Click driver failed: {errors}")
            click_values = cast(
                list[float],
                json.loads(str(javascript(window, pump, "JSON.stringify(r09.samples)"))),
            )[warmup:]
            if javascript(window, pump, "r09.trusted.every(Boolean)") is not True:
                raise RuntimeError("Click driver did not deliver native trusted input")
            memory_after = {
                "host": windows_memory(os.getpid()),
                "renderer": windows_memory(window.web.page().renderProcessPid()),
            }
            screen = window.screen()
            return {
                "scenario": asdict(case),
                "synthetic": True,
                "fixture_json_sha256": hashlib.sha256(
                    project.model_dump_json().encode()
                ).hexdigest(),
                "result_cells": case.rows * case.lanes,
                "thumbnail_size": [128, 128],
                "snapshot_utf8_bytes": {"min": min(byte_counts), "max": max(byte_counts)},
                "timings": timings,
                "idle_publish_ms": distribution(idle),
                "idle_snapshot_calls": idle_calls,
                "idle_state_emissions": len(emitted),
                "refresh_click_ms": distribution(click_values),
                "refresh_handler_ms": distribution(
                    cast(
                        list[float],
                        json.loads(
                            str(javascript(window, pump, "JSON.stringify(r09.handlerSamples)"))
                        ),
                    )[warmup:]
                ),
                "native_clicks": True,
                "memory_before": memory_before,
                "memory_after": memory_after,
                "qt": qVersion(),
                "qpa": QApplication.platformName(),
                "screen": {
                    "width": screen.size().width(),
                    "height": screen.size().height(),
                    "device_pixel_ratio": screen.devicePixelRatio(),
                    "logical_dpi": screen.logicalDotsPerInch(),
                },
                "viewport": [window.web.width(), window.web.height()],
                "cleanup": "normal close/drain/deleteLater helper required before report returns",
            }
        finally:
            window.close()
            if window.shutdown_stage == "confirm_draft":
                window.bridge.session("reply", '{"choice":"discard"}')
            if window.shutdown_stage == "confirm_dirty":
                window.bridge.session("reply", '{"choice":"discard"}')
            # Reuse the existing helper's normal host shutdown and prompt replies. EventPump
            # implements its only consumed QtBot method; no pytest fixture or fake lifecycle.
            close_and_dispose_window(
                window,
                cast("QtBot", pump),
                resources_closed=lambda: window.host.resources_closed,
                timeout=30000,
            )
            QTest.qWait(30)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=SCENARIOS, default="rows-small")
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-fixtures", action="store_true")
    parser.add_argument(
        "--run", action="store_true", help="Open one native window and measure one case"
    )
    args = parser.parse_args()
    if args.validate_fixtures:
        assert distribution(list(range(1, 101)))["p95"] == 95
        for scenario in SCENARIOS.values():
            project, rasters = fixture(scenario)
            assert len(project.rows) == len(rasters) == scenario.rows
            assert len(cells(project)) == scenario.rows * scenario.lanes
            assert all(len(raster.pixels) == 128**2 for raster in rasters)
            print(f"Validated {scenario.name}: {scenario.rows} rows, {scenario.lanes} lanes")
        return 0
    if not args.run:
        print(
            json.dumps(
                {
                    "scenarios": [asdict(item) for item in SCENARIOS.values()],
                    "engineering_triggers": BUDGETS,
                    "samples": args.samples,
                    "warmup": args.warmup,
                    "performance_measured": False,
                },
                indent=2,
            )
        )
        return 0
    if (
        args.output is None
        or args.output.exists()
        or not 20 <= args.samples <= 100
        or not 1 <= args.warmup <= 10
    ):
        parser.error("Use a new --output path, 20..100 samples and 1..10 warmups")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise RuntimeError("Commit/freeze the benchmark and product before performance measurement")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    result = {
        "schema": 1,
        "commit": commit,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python": sys.version,
        "cpu_count": os.cpu_count(),
        "environment": {
            name: os.environ.get(name)
            for name in (
                "QT_QPA_PLATFORM",
                "QT_OPENGL",
                "QTWEBENGINE_CHROMIUM_FLAGS",
                "QT_QUICK_BACKEND",
            )
        },
        "budgets_frozen_before_measurement": BUDGETS,
        "warmup": args.warmup,
        "measurement": measure(SCENARIOS[args.case], args.samples, args.warmup),
        "scope": "Synthetic metadata/thumbnail/bridge/renderer only; not real-project acceptance",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
