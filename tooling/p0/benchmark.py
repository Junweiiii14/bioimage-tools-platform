"""Fixed corpus and real worker processes; no desktop input is synthesized here."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path
from typing import Literal

from PySide6.QtCore import QCoreApplication, QTimer

from tooling.p0.controller import Controller
from tooling.p0.metrics import summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--executable", type=Path)
    args = parser.parse_args()
    root: Path = args.fixtures.resolve()
    output: Path = args.output
    if output.exists():
        raise FileExistsError(output)
    app = QCoreApplication([])
    worker_command = [str(args.executable.resolve()), "--worker"] if args.executable else None
    host = Controller(worker_command=worker_command)
    scenarios: list[tuple[str, list[Path], Literal["normal", "crash", "stubborn"]]] = []
    for name in ["灰度2048.tif", "灰度4096.tif", "彩色4096.tif"]:
        scenarios.extend((name, [root / name], "normal") for _ in range(5))
    scenarios.extend(
        ("batch20", [root / f"批次{i:02d}.tif" for i in range(20)], "normal") for _ in range(3)
    )
    scenarios.extend(
        [
            ("crash", [root / "灰度2048.tif"], "crash"),
            ("recovery", [root / "灰度2048.tif"], "normal"),
            ("cooperative-cancel", [root / "灰度4096.tif"] * 20, "normal"),
            ("forced-cancel", [root / "灰度2048.tif"], "stubborn"),
        ]
    )
    index = 0
    elapsed: dict[str, list[float]] = {}
    failed = False

    def next_run() -> None:
        nonlocal index, failed
        if host.history:
            label = scenarios[index - 1][0]
            result = host.history[-1]
            result["scenario"] = label
            result["sample_ordinal"] = index
            expected = (
                "failed"
                if label == "crash"
                else ("cancelled" if "cancel" in label else "succeeded")
            )
            failed |= result["outcome"] != expected
            elapsed.setdefault(label, []).append(float(str(result["elapsed_seconds"])))
            print(label, result["outcome"], f"{elapsed[label][-1]:.3f}s", flush=True)
        if index == len(scenarios):
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("x", encoding="utf-8") as stream:
                json.dump(
                    {
                        "schema": 1,
                        "environment": platform.platform(),
                        "worker_command": host.worker_command,
                        "passes": 3,
                        "statistic": (
                            "nearest-rank p95; fresh process per run; filesystem cache not flushed"
                        ),
                        "seconds_by_scenario": {
                            key: summary(value) for key, value in elapsed.items()
                        },
                        "runs": host.history,
                    },
                    stream,
                    ensure_ascii=False,
                    indent=2,
                )
            app.quit()
            return
        label, paths, mode = scenarios[index]
        index += 1
        host.start(paths, mode=mode)
        if "cancel" in label:
            QTimer.singleShot(1200, host.cancel)

    host.ended.connect(next_run)
    QTimer.singleShot(0, next_run)
    app.exec()
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
