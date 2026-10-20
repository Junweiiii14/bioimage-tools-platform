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
    if len(sys.argv) == 3 and sys.argv[1] == "--verify-installation":
        from pathlib import Path

        from bioimage_app.installation_check import verify_installation

        return verify_installation(Path(sys.argv[2]))
    if len(sys.argv) == 3 and sys.argv[1] == "--verify-intake-installation":
        from pathlib import Path

        from bioimage_app.installation_check_intake import verify_intake_installation

        return verify_intake_installation(Path(sys.argv[2]))
    from bioimage_app.desktop_entry import create_desktop_window, desktop_mode

    mode = desktop_mode(sys.argv[1:])
    from pathlib import Path

    from PySide6.QtCore import QStandardPaths
    from PySide6.QtWidgets import QApplication

    from bioimage_app.diagnostics import DesktopDiagnostics

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
    window = create_desktop_window(mode)
    window.show()
    try:
        return app.exec()
    finally:
        if diagnostics is not None:
            diagnostics.close()


if __name__ == "__main__":
    raise SystemExit(main())
