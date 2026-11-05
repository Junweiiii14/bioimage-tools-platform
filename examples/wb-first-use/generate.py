"""Create nonexperimental WB practice inputs in a new directory only."""

import argparse
from pathlib import Path

import numpy as np
import tifffile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    destination = parser.parse_args().destination
    # Refuse existing destinations, including originals or prior practice results.
    destination.mkdir(parents=True, exist_ok=False)
    inputs = destination / "inputs"
    inputs.mkdir()
    # Reuse the zero-angle, marker-free geometry of test_source_geometry.membrane.
    yy, xx = np.mgrid[:300, :700]
    u, v = xx - 350, yy - 150
    raw = np.full(xx.shape, 15, dtype=np.uint16)
    raw[(np.abs(u) < 130) & (np.abs(v) < 45)] = 50000
    for index in range(5):
        raw[(np.abs(u - (-96 + index * 48)) < 17) & (np.abs(v) < 7)] = 8000 if index % 2 else 20000
    tifffile.imwrite(inputs / "A_123456 (1).tiff", raw)
    raw[0, 0] += 1  # Distinct source identity; outside the membrane and all bands.
    tifffile.imwrite(inputs / "B_123456 (1).tiff", raw)
    print(inputs.resolve())


if __name__ == "__main__":
    main()
