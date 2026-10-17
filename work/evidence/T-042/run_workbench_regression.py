"""Real Qt host import/worker/save/export/reopen, with source paths only and no injected results."""

import faulthandler
import json
import sys
import time
from hashlib import sha256
from pathlib import Path

from bioimage_app.api import create_figure_project_window
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication


def main() -> None:
    faulthandler.enable()
    faulthandler.dump_traceback_later(60, repeat=True)
    manifest, destination = Path(sys.argv[1]), Path(sys.argv[2])
    entries = json.loads(manifest.read_text(encoding="utf-8"))
    assert all(set(e) == {"path", "sha256"} for e in entries)
    assert not destination.exists()
    application = QApplication([])
    window = create_figure_project_window()
    window.automatic.crop_policy = "source_geometry@2"
    window.automatic.quant_policy = sys.argv[3] if len(sys.argv) > 3 else "wbquant_1_4_3@1"

    def wait(predicate, seconds=180):
        deadline = time.monotonic() + seconds
        last_status = None
        while not predicate():
            status = window.view.status.text()
            if status != last_status:
                print(status, flush=True)
                last_status = status
            if time.monotonic() > deadline:
                raise TimeoutError(window.view.status.text())
            application.processEvents()
            QTest.qWait(25)

    try:
        window.show()
        window.open_workspace(str(destination), create=True)
        wait(lambda: not window.operation_busy)
        window.import_images(tuple(e["path"] for e in entries), automatic=True)
        wait(
            lambda: (
                bool(window.automatic.last_output_path) or "操作失败" in window.view.status.text()
            ),
            300,
        )
        assert window.automatic.last_output_path, window.view.status.text()
        wait(lambda: not window.operation_busy)
        project = window.view.project()
        assert len(project.rows) == len(entries)
        assert all(row.roi is not None for row in project.rows)
        assert all(
            plan.run is not None and plan.run.state == "succeeded" for plan in project.analyses
        )
        assert len(project.analyses) == len(entries)
        document = project.project_id
        encoded = project.model_dump_json()
        output = Path(window.automatic.last_output_path)
        window.load_document(document)
        wait(lambda: not window.operation_busy)
        assert window.view.project().model_dump_json() == encoded
        window.grab().save(str(destination / "workbench.png"))
        for e in entries:
            assert sha256(Path(e["path"]).read_bytes()).hexdigest() == e["sha256"]
        report = {
            "source_count": len(entries),
            "lane_counts": [row.lane_count for row in project.rows],
            "runs": len(project.analyses),
            "output": str(output),
            "source_hashes_unchanged": True,
            "reopen_equal": True,
            "reference_reads": False,
            "status": window.view.status.text(),
        }
        (destination / "validation.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(report, ensure_ascii=True), flush=True)
    finally:
        window.close()
        wait(lambda: window.resources_closed, 60)
    application.processEvents()


if __name__ == "__main__":
    main()
