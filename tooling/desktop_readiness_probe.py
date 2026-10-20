"""Fresh-process offscreen desktop DOM readiness; no user workspace or settings."""

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from tooling.p0.metrics import peak_memory, summary


def child() -> int:
    from PySide6.QtCore import QSettings, QTimer
    from PySide6.QtWidgets import QApplication
    from shiboken6 import isValid

    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    from bioimage_app.web_window import WebWorkbenchWindow

    with TemporaryDirectory(prefix="wb-readiness-") as temporary:
        settings = QSettings(str(Path(temporary) / "probe.ini"), QSettings.Format.IniFormat)
        window = WebWorkbenchWindow(settings=settings)
        window.show()
        since = time.monotonic()
        closing = disposing = pending = False
        failed = False
        timer = QTimer(app)

        def received(value: object) -> None:
            nonlocal pending, closing
            pending = False
            if value is True and not closing:
                print(
                    "READY "
                    + json.dumps({"ready_ns": time.time_ns(), "peak_rss_bytes": peak_memory()}),
                    flush=True,
                )
                closing = True
                window.close()

        def poll() -> None:
            nonlocal closing, disposing, pending, failed
            if disposing:
                if not isValid(window):
                    timer.stop()
                    app.exit(int(failed))
                return
            if time.monotonic() - since > 20:
                failed = True
                if not closing:
                    closing = True
                    window.close()
                if time.monotonic() - since > 30:
                    timer.stop()
                    app.exit(1)
                return
            if closing:
                if window.host.resources_closed:
                    disposing = True
                    window.deleteLater()
                return
            if not pending:
                pending = True
                window.web.page().runJavaScript(
                    "typeof bridge !== 'undefined' && bridge !== null && "
                    "document.readyState === 'complete' && "
                    "document.querySelector('#home-view')?.hidden === false",
                    received,
                )

        timer.timeout.connect(poll)
        timer.start(10)
        return app.exec()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--n", type=int, default=20)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.child:
        return child()
    if args.n < 1 or args.output is None:
        raise ValueError("Positive n and a new output path are required")
    from pydantic import TypeAdapter

    samples: list[dict[str, float | int]] = []
    with args.output.open("x", encoding="utf-8") as stream:
        for index in range(args.n):
            before_ns = time.time_ns()
            started = time.perf_counter()
            result = subprocess.run(
                [sys.executable, "-m", "tooling.desktop_readiness_probe", "--child"],
                env={
                    **os.environ,
                    "QT_QPA_PLATFORM": "offscreen",
                    **{
                        key: "1"
                        for key in (
                            "OMP_NUM_THREADS",
                            "OPENBLAS_NUM_THREADS",
                            "MKL_NUM_THREADS",
                            "NUMEXPR_NUM_THREADS",
                        )
                    },
                },
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            if result.returncode:
                sys.stderr.write(result.stderr)
                result.check_returncode()
            completed = time.perf_counter() - started
            ready = next(
                line[6:] for line in result.stdout.splitlines() if line.startswith("READY ")
            )
            sample = TypeAdapter(dict[str, int]).validate_json(ready)
            seconds = (sample["ready_ns"] - before_ns) / 1e9
            if not 0 < seconds < completed:
                raise ValueError("Readiness clock is outside the owned process lifetime")
            samples.append(
                {
                    "ready_seconds": seconds,
                    "whole_process_seconds": completed,
                    "peak_rss_bytes": sample["peak_rss_bytes"],
                }
            )
            print(index + 1, seconds, flush=True)
        json.dump(
            {
                "environment": platform.platform(),
                "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "n": args.n,
                "samples": samples,
                "ready_seconds": summary([s["ready_seconds"] for s in samples]),
                "limitations": (
                    "Offscreen fresh interpreter to real DOM/WebChannel home readiness, "
                    "including process creation, default numerical thread limits. "
                    "Isolated settings, excludes normal diagnostics log startup. "
                    "Not native paint/input/DPI; OS caches not flushed. GUI-process RSS only, "
                    "excludes renderer children. Every child normally closes resources and "
                    "deletes its owned window before exit."
                ),
            },
            stream,
            indent=2,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
