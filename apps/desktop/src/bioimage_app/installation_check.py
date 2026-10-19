"""Explicit local diagnostic: synthetic TIFF, durable worker, offline OCR, and Qt exit."""

import json
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
from typing import cast


def verify_installation(report_path: Path) -> int:
    import numpy as np
    import tifffile
    from PySide6.QtCore import QSettings, QTimer
    from PySide6.QtWidgets import QApplication
    from wb_tool.api import recognize_figure

    from bioimage_app.web_window import WebWorkbenchWindow

    # Refuse replacement of any user-provided existing output.
    with (
        report_path.open("x", encoding="utf-8") as report,
        tempfile.TemporaryDirectory(prefix="bioimage-install-check-") as temporary,
        ThreadPoolExecutor(max_workers=1) as executor,
    ):
        root = Path(temporary)
        originals = root / "originals"
        originals.mkdir()
        source = originals / "synthetic.tif"
        pixels = np.full((90, 180), 50000, dtype=np.uint16)
        pixels[35:45, 40:65] = 10000
        pixels[35:45, 110:135] = 15000
        tifffile.imwrite(source, pixels)
        before = sha256(source.read_bytes()).hexdigest()
        settings = QSettings(str(root / "settings.ini"), QSettings.Format.IniFormat)
        settings.setValue("project_parent", str(root / "projects"))
        app = QApplication(["BioImage installation diagnostic"])
        window = WebWorkbenchWindow(settings=settings)
        window.show()
        window.start_from_images([source], automatic=False)
        started = time.monotonic()
        phase = "import"
        errors: list[str] = []
        checks: list[str] = []
        future = None

        def record() -> None:
            state = {
                "phase": phase,
                "errors": errors,
                "elapsed": time.monotonic() - started,
                "status": window.host.view.status.text(),
            }
            report.seek(0)
            report.truncate()
            report.write(json.dumps(state, ensure_ascii=False, indent=2))
            report.flush()

        def poll() -> None:
            nonlocal phase, future
            try:
                if time.monotonic() - started > 90 and phase != "close":
                    errors.append("Diagnostic exceeded 90 seconds")
                    phase = "close"
                    window.close()
                if phase == "close":
                    if window.shutdown_stage == "confirm_busy":
                        window.bridge.session("reply", '{"choice":"cancel"}')
                    elif window.shutdown_stage == "confirm_dirty":
                        window.bridge.session("reply", '{"choice":"save"}')
                    return
                if window.host.operation_busy or window.shutdown_stage != "idle":
                    return
                project = window.host.view.project()
                if phase == "import" and project.rows and not window.host.has_unsaved_changes:
                    phase = "target"
                    window.bridge.request(
                        "quant_select",
                        json.dumps({"id": project.rows[0].row_id, "overview": False}),
                    )
                    record()
                elif phase == "target":
                    snapshot = window.bridge.snapshot()
                    quant = cast(dict[str, object], snapshot["quant"])
                    original = project.rows[0].source
                    if original is None:
                        raise ValueError("Synthetic original reference is missing")
                    target = {
                        "projectId": project.project_id,
                        "id": project.rows[0].row_id,
                        "sourceId": original.sha256,
                        "revision": quant["revision"],
                        "n": 2,
                        "polarity": "dark",
                        "emptyLanes": [],
                        "roi": {"x": 20, "y": 10, "width": 140, "height": 70},
                        "laneRois": [
                            {"x": 20, "y": 10, "width": 60, "height": 70},
                            {"x": 100, "y": 10, "width": 60, "height": 70},
                        ],
                    }
                    window.bridge.request("quant_target", json.dumps(target))
                    if not window.host.operation_busy:
                        raise ValueError(
                            "Worker did not start: " + str(window.bridge.snapshot()["status"])
                        )
                    phase = "worker"
                    record()
                elif phase == "worker" and window.host.project_results:
                    if len(window.host.view.analysis.result_view.cells) != 2:
                        raise ValueError("Synthetic two-lane worker did not commit two results")
                    checks.append("durable-worker")
                    future = executor.submit(recognize_figure, str(source), before)
                    phase = "ocr"
                    record()
                elif phase == "ocr" and future is not None and future.done():
                    future.result()
                    if sha256(source.read_bytes()).hexdigest() != before:
                        raise ValueError("Synthetic original was modified")
                    checks.append("offline-ocr")
                    phase = "close"
                    record()
                    window.close()
            except (ValueError, OSError, RuntimeError, ImportError) as error:
                errors.append(str(error))
                phase = "close"
                record()
                window.close()

        timer = QTimer(window)
        timer.setInterval(150)
        timer.timeout.connect(poll)
        timer.start()
        record()
        code = app.exec()
        timer.stop()
        if code or not window.host.resources_closed:
            errors.append("Application did not finish its owned resource shutdown")
        if "offline-ocr" not in checks and not errors:
            errors.append("Diagnostic stopped before completing the worker and OCR checks")
        phase = "failed" if errors else "passed"
        record()
        if sys.stdout is not None:
            print("Installation diagnostic:", phase, flush=True)
        return 1 if errors else 0
