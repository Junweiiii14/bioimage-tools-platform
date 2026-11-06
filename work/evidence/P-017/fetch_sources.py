"""Fetch fixed public research files; never execute downloaded code."""

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

root = Path(sys.argv[1])
manifest = json.loads(Path(__file__).with_name("source-manifest.json").read_text())
for item in manifest["files"]:
    target = root / item["path"]
    if target.exists():
        data = target.read_bytes()
    else:
        url = (
            "https://raw.githubusercontent.com/mdc-science/plateReadeR/"
            + manifest["commit"]
            + "/"
            + item["path"]
        )
        data = urllib.request.urlopen(url, timeout=60).read()
        assert hashlib.sha256(data).hexdigest() == item["sha256"], item["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    assert hashlib.sha256(data).hexdigest() == item["sha256"], item["path"]
    print(item["path"], item["sha256"])
