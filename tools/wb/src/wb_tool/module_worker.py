"""Static, no-GUI comparison worker entry; native thread limits precede imports."""

import os


def main() -> int:
    for name in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        os.environ[name] = "1"
    from wb_tool.adapters.module_worker import main as run

    return run()


if __name__ == "__main__":
    raise SystemExit(main())
