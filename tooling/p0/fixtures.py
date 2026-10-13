"""Generate deterministic public synthetic TIFFs, never overwrite existing files."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import tifffile


def generate(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=False)
    records: list[dict[str, object]] = []
    for name, size, channels, offset in [
        ("灰度2048.tif", 2048, 1, 0),
        ("灰度4096.tif", 4096, 1, 0),
        ("彩色4096.tif", 4096, 3, 0),
        *[(f"批次{i:02d}.tif", 4096, 1, i) for i in range(20)],
    ]:
        yy = np.arange(size, dtype=np.uint32)[:, None]
        xx = np.arange(size, dtype=np.uint32)[None, :]
        gray = ((xx * 17 + yy * 31 + offset * 101) % 65536).astype(np.uint16)
        data = (
            gray
            if channels == 1
            else np.stack(
                [
                    (gray // 256).astype(np.uint8),
                    (gray % 256).astype(np.uint8),
                    ((gray // 128) % 256).astype(np.uint8),
                ],
                axis=2,
            )
        )
        path = root / name
        tifffile.imwrite(
            path, data, photometric="minisblack" if channels == 1 else "rgb", metadata=None
        )
        with path.open("rb") as stream:
            checksum = hashlib.file_digest(stream, "sha256").hexdigest()
        records.append(
            {
                "file": name,
                "shape": list(data.shape),
                "dtype": str(data.dtype),
                "sha256": checksum,
            }
        )
    (root / "manifest.json").write_text(
        json.dumps(
            {"generator": "p0-v1: (17*x+31*y+101*i)%65536", "files": records},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    generate(parser.parse_args().directory)
