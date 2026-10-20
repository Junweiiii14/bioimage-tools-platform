"""Fixed packaged candidate entry; never imports code from the current directory."""

import os

for variable in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ[variable] = "1"
os.environ["BIOIMAGE_RELEASE_CHANNEL"] = "candidate"

from bioimage_app.api import run_application  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(run_application())
