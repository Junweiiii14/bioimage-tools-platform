"""Static desktop entry; limit numerical threads before importing tool registration."""

import os
import sys

for variable in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ[variable] = "1"


def main() -> int:
    if sys.argv[1:] == ["--worker", "wb"]:
        from wb_tool.api import run_wb_worker

        return run_wb_worker()
    if sys.argv[1:] == ["--worker", "wb_ocr"]:
        from wb_tool.api import run_ocr_worker

        return run_ocr_worker()
    from pathlib import Path

    from PySide6.QtCore import QStandardPaths
    from PySide6.QtWidgets import QApplication

    from bioimage_app.diagnostics import DesktopDiagnostics
    from bioimage_app.wb_window import WBWindow

    app = QApplication(sys.argv)
    app.setApplicationName("BioImageTools")
    diagnostics: DesktopDiagnostics | None = None
    try:
        diagnostics = DesktopDiagnostics(
            Path(
                QStandardPaths.writableLocation(
                    QStandardPaths.StandardLocation.AppLocalDataLocation
                )
            )
            / "logs"
        )
    except OSError:
        print("无法创建本地诊断日志；继续启动。", file=sys.stderr)
    window = WBWindow()
    window.show()
    try:
        return app.exec()
    finally:
        if diagnostics is not None:
            diagnostics.close()


if __name__ == "__main__":
    raise SystemExit(main())
