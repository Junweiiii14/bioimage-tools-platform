"""Accepted Qt jobs reply once, including cancellation and recoverable faults."""

import json
from collections.abc import Callable, Iterator
from pathlib import Path
from threading import Event
from typing import cast

import numpy as np
import pytest
import tifffile
from bioimage_app.diagnostics import DesktopDiagnostics
from bioimage_app.figure_window import FigureProjectWindow
from PySide6.QtCore import QMetaObject, QObject, Qt, QThread
from pytestqt.qtbot import QtBot
from shiboken6 import isValid
from tool_contracts.api import AssetRef
from wb_tool.adapters import fig_quant, ocr
from wb_tool.api import FigureRow, LoadedTiff, WBFigureProject, WBJob, WBReply, load_tiff
from wb_tool.ui import background

from tooling.qt_test_lifecycle import close_and_dispose_window


def attribute(owner: object, name: str) -> object:
    """Inspect owned internals without adding a public testing API."""
    return getattr(owner, name)


@pytest.fixture
def terminal_port(qtbot: QtBot) -> Iterator[background.WBBackground]:
    port = background.WBBackground()
    closed: list[bool] = []
    port.closed.connect(lambda: closed.append(True))
    try:
        yield port
    finally:
        if not closed:
            # Teardown only: queue retirement after the finite injected operation.
            # Never clear pending or use this route as evidence of successful drain.
            worker = cast(QObject, attribute(port, "_work"))
            QMetaObject.invokeMethod(worker, "retire", Qt.ConnectionType.QueuedConnection)
            qtbot.waitUntil(lambda: bool(closed), timeout=5000)
        port.deleteLater()
        qtbot.waitUntil(lambda: not isValid(port), timeout=5000)


def source_project(tmp_path: Path, width: int = 4) -> tuple[Path, WBFigureProject]:
    path = tmp_path / "tiny.tif"
    tifffile.imwrite(path, np.full((4, width), 100, dtype=np.uint8))
    image = load_tiff(path)
    project = WBFigureProject(
        project_id="unchanged",
        rows=(
            FigureRow(
                row_id="sheet",
                source=AssetRef(
                    asset_id="source",
                    relative_path="assets/source.tif",
                    sha256=image.sha256,
                    size_bytes=path.stat().st_size,
                ),
                filename=path.name,
                width=width,
                height=4,
                bit_depth=8,
            ),
        ),
        figure_order=("Fig1",),
    )
    return path, project


@pytest.mark.parametrize("phase", ["before", "decode", "tile", "memory", "runtime"])
@pytest.mark.parametrize("close_during", [False, True])
def test_fault_and_cancel_reply_once_and_drain(
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    terminal_port: background.WBBackground,
    phase: str,
    close_during: bool,
) -> None:
    port = terminal_port
    path, project = source_project(tmp_path, 2050 if phase == "tile" else 4)
    frozen = project.model_dump_json()
    cancellation, entered, release = Event(), Event(), Event()
    actual_load = load_tiff
    calls: list[str] = []

    def wait_for_release() -> None:
        entered.set()
        if not release.wait(5):
            raise TimeoutError("test did not release controlled operation")

    def decoded(source: str | Path) -> LoadedTiff:
        result = actual_load(source)
        calls.append("decode")
        wait_for_release()
        return result

    def failed(source: str | Path) -> LoadedTiff:
        wait_for_release()
        if phase == "memory":
            raise MemoryError()  # Empty messages must still be failed, never success.
        raise RuntimeError("controlled failure")

    if phase == "before":
        cancellation.set()
    elif phase == "decode":
        monkeypatch.setattr(fig_quant, "load_tiff", decoded)
    elif phase == "tile":
        # Exercise the actual OCR tiling cancellation boundary without model inference.
        import rapidocr
        from rapidocr.utils.output import RapidOCROutput

        def tile(_pixels: object) -> RapidOCROutput:
            calls.append("tile")
            wait_for_release()
            return RapidOCROutput()

        def engine_factory(**_kwargs: object) -> Callable[[object], RapidOCROutput]:
            return tile

        def verified_models(_path: Path) -> tuple[tuple[str, str], ...]:
            return ()

        monkeypatch.setattr(rapidocr, "RapidOCR", engine_factory)
        monkeypatch.setattr(ocr, "verify_ocr_models", verified_models)
    else:
        monkeypatch.setattr(background, "load_tiff", failed)

    replies: list[WBReply] = []
    closed: list[bool] = []
    port.replied.connect(replies.append)
    port.closed.connect(lambda: closed.append(True))
    thread = port.findChild(QThread)
    assert thread is not None
    try:
        with qtbot.captureExceptions() as escaped:
            request_id = port.submit(
                WBJob(
                    "preview" if phase in {"memory", "runtime"} else "quant_fig",
                    path=str(path),
                    document=project,
                    row_id="sheet",
                    cancellation=cancellation,
                )
            )
            if phase != "before":
                qtbot.waitUntil(entered.is_set, timeout=5000)
                if phase in {"decode", "tile"}:
                    cancellation.set()
            if close_during:
                port.shutdown()
                assert not closed and thread.isRunning()
            release.set()
            qtbot.waitUntil(lambda: bool(replies) or bool(escaped), timeout=5000)
            assert not escaped, "An accepted request escaped the terminal boundary"
            assert len(replies) == 1
            reply = replies[0]
            assert reply.request_id == request_id and reply.value is None and reply.error
            assert not attribute(port, "_pending")
            assert project.model_dump_json() == frozen
            if phase in {"before", "decode", "tile"}:
                assert "取消" in reply.error
            else:
                assert ("MemoryError" if phase == "memory" else "RuntimeError") in reply.error
            if phase == "tile":
                assert calls == ["tile"]
            if not close_during:
                # Same real queue remains usable, independent of the failed adapter.
                recovery_id = port.submit(WBJob("encode", document=project))
                qtbot.waitUntil(lambda: len(replies) == 2, timeout=5000)
                assert replies[-1].request_id == recovery_id and not replies[-1].error
                assert replies[-1].value == frozen.encode("utf-8")
                assert not attribute(port, "_pending")
                port.shutdown()
            qtbot.waitUntil(lambda: bool(closed), timeout=5000)
            assert closed == [True] and not thread.isRunning()
            assert len(replies) == (1 if close_during else 2)
    finally:
        release.set()


@pytest.mark.parametrize("exception", [KeyboardInterrupt, SystemExit])
def test_process_exit_signals_are_not_swallowed(
    exception: type[BaseException], monkeypatch: pytest.MonkeyPatch
) -> None:
    factory = cast(Callable[[], QObject], attribute(background, "_Work"))
    worker = factory()
    replies: list[WBReply] = []
    from PySide6.QtCore import SignalInstance

    signal = cast(SignalInstance, attribute(worker, "replied"))
    signal.connect(replies.append)
    # No Qt queued delivery for process-exit signals. Inspect the slot directly.
    execute = cast(Callable[[str, WBJob], None], attribute(worker, "execute"))

    def stop(_source: str) -> LoadedTiff:
        raise exception()

    monkeypatch.setattr(background, "load_tiff", stop)

    try:
        with pytest.raises(exception):
            execute("exit", WBJob("preview"))
        assert not replies
    finally:
        worker.deleteLater()


@pytest.mark.parametrize("action", ["cancel", "close", "failure", "newer_draft"])
def test_fig_host_keeps_project_and_retires_after_fault(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, action: str
) -> None:
    path, _ = source_project(tmp_path)
    window = FigureProjectWindow()
    entered, release = Event(), Event()
    actual_load = load_tiff

    def controlled(source: str | Path) -> LoadedTiff:
        image = actual_load(source)
        entered.set()
        if not release.wait(5):
            raise TimeoutError("host did not release operation")
        if action in {"failure", "newer_draft"}:
            raise MemoryError()
        return image

    try:
        window.open_workspace(str(tmp_path / "workspace"), create=True)
        qtbot.waitUntil(lambda: bool(window.workspace_path) and not window.operation_busy)
        window.import_images((str(path),))
        qtbot.waitUntil(
            lambda: len(window.view.project().rows) == 1 and not window.operation_busy,
            timeout=10000,
        )
        window.save()
        qtbot.waitUntil(lambda: not window.operation_busy, timeout=10000)
        project = window.view.project()
        frozen = project.model_dump_json()
        monkeypatch.setattr(fig_quant, "load_tiff", controlled)
        window.analyze_fig_sheet(project.rows[0].row_id)
        qtbot.waitUntil(entered.is_set, timeout=5000)
        if action == "close":
            window.close()
            assert not window.resources_closed
        elif action == "cancel":
            window.cancel()
        elif action == "newer_draft":
            updated = project.model_copy(
                update={"rows": (project.rows[0].model_copy(update={"protein": "newer"}),)}
            )
            window.view.set_project(updated)
            window.view.generation += 1
            frozen = window.view.project().model_dump_json()
        release.set()
        qtbot.waitUntil(lambda: not window.operation_busy, timeout=10000)
        assert window.view.project().model_dump_json() == frozen
        if action == "failure":
            assert "MemoryError" in window.operation_error
        if action == "close":
            qtbot.waitUntil(lambda: window.resources_closed, timeout=10000)
        else:
            # Real host save/encode after failure/cancel must still complete.
            window.save()
            qtbot.waitUntil(lambda: not window.operation_busy, timeout=10000)
    finally:
        release.set()
        close_and_dispose_window(
            window, qtbot, resources_closed=lambda: window.resources_closed, timeout=10000
        )


@pytest.mark.parametrize("broken_logger", [False, True])
def test_failure_diagnostic_is_bounded_and_cannot_suppress_reply(
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    terminal_port: background.WBBackground,
    broken_logger: bool,
) -> None:
    port = terminal_port
    replies: list[WBReply] = []
    port.replied.connect(replies.append)

    def failed(_path: str) -> LoadedTiff:
        raise RuntimeError("private-image-path-and-payload")

    def failed_log(_message: str) -> None:
        raise MemoryError()

    monkeypatch.setattr(background, "load_tiff", failed)
    if broken_logger:
        monkeypatch.setattr(background, "qWarning", failed_log)
    diagnostics = DesktopDiagnostics(tmp_path / "diagnostics")
    try:
        request_id = port.submit(WBJob("preview", path="private-source-path", revision=7))
        qtbot.waitUntil(lambda: bool(replies), timeout=5000)
        assert len(replies) == 1 and replies[0].error and replies[0].value is None
        records = [
            json.loads(line) for line in diagnostics.path.read_text(encoding="utf-8").splitlines()
        ]
        failures = [item["message"] for item in records if "WB job failed" in item["message"]]
        assert len(failures) == (0 if broken_logger else 1)
        if not broken_logger:
            message = failures[0]
            assert (
                request_id in message and "operation=preview" in message and "revision=7" in message
            )
            assert "RuntimeError" in message and "test_wb_background_terminal.py" in message
            assert "private-image-path" not in message and "private-source-path" not in message
        with qtbot.waitSignal(port.closed, timeout=5000):
            port.shutdown()
    finally:
        diagnostics.close()
