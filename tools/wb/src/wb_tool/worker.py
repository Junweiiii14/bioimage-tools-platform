"""Static worker entry point; numerical thread limits precede library loading."""

import os


def main() -> int:
    for name in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        os.environ[name] = "1"
    from wb_tool.adapters.worker import main as run

    return run()


if __name__ == "__main__":
    raise SystemExit(main())
