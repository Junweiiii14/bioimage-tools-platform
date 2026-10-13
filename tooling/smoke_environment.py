"""Exercise installed libraries with synthetic data, not product acceptance."""

from __future__ import annotations

import json
import os
import subprocess
import sys


def main() -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    code = """
import json, tempfile
from pathlib import Path
import numpy as np
import scipy
import tifffile
import PIL
import pydantic
import PySide6
from PySide6.QtCore import QProcess
from PySide6.QtWidgets import QApplication, QWidget
app = QApplication([])
widget = QWidget()
widget.resize(320, 240)
widget.show()
app.processEvents()
with tempfile.TemporaryDirectory(prefix='bioimage-') as temp:
    path = Path(temp) / '中文路径' / '16位.tif'
    path.parent.mkdir()
    original = np.arange(4096, dtype=np.uint16).reshape(64, 64)
    tifffile.imwrite(path, original)
    loaded = tifffile.imread(path)
    assert loaded.dtype == np.uint16 and np.array_equal(original, loaded)
worker = QProcess()
worker.start(__import__('sys').executable, ['-c', 'print("worker-ok")'])
assert worker.waitForFinished(10000), 'environment probe worker timed out'
assert worker.exitCode() == 0
assert bytes(worker.readAllStandardOutput()).strip() == b'worker-ok'
widget.close()
print(json.dumps({'qt': PySide6.__version__, 'numpy': np.__version__,
 'scipy': scipy.__version__, 'pillow': PIL.__version__,
 'pydantic': pydantic.__version__, 'utf8_uint16_tiff': 'passed',
 'qprocess': 'passed', 'offscreen_widget': 'passed',
 'scope': 'environment only; no DPI, cancellation or packaged-product validation'}))
"""
    result = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", code],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=45,
        check=False,
    )
    if result.returncode:
        print(result.stderr)
        return result.returncode
    print(json.dumps(json.loads(result.stdout), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
