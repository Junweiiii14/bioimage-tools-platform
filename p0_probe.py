"""P0 executable: dispatch worker before importing any Qt module."""

from __future__ import annotations

import os
import sys
import time

STARTED = time.perf_counter()


def main() -> int:
    for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[name] = "1"
    if "--worker" in sys.argv:
        from tooling.p0.worker import main as worker_main

        return worker_main()
    from tooling.p0.gui import main as gui_main

    return gui_main(STARTED)


if __name__ == "__main__":
    raise SystemExit(main())
