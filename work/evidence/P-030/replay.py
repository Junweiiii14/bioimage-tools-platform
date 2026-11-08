"""Reproduce the four-frame batch in a fresh directory (Java executable as argv[2])."""

import hashlib
import json
import struct
import subprocess
import sys
import zlib
from pathlib import Path
from urllib.request import Request, urlopen

root = Path(sys.argv[1]).resolve()
root.mkdir(exist_ok=False)
for folder in ["images", "labels", "out/data"]:
    (root / folder).mkdir(parents=True)
archive = "https://zenodo.org/api/records/21779854/files/dataset.zip/content"
manifest = json.loads(Path(__file__).with_name("manifest.json").read_text())
for row in manifest:
    for kind in ("images", "labels"):
        entry = row[kind]
        start, end = entry["range"]
        request = Request(f"{archive}?r={start}", headers={"Range": f"bytes={start}-{end}"})
        with urlopen(request, timeout=90) as response:
            if response.status != 206:
                raise RuntimeError("Archive server did not honor byte range")
            block = response.read(end - start + 1)
        header = struct.unpack_from("<4s5H3L2H", block)
        filename_end = 30 + header[-2]
        assert header[0] == b"PK\x03\x04" and header[3] in (0, 8)
        assert block[30:filename_end].decode() == entry["path"]
        offset = filename_end + header[-1]
        payload = block[offset : offset + entry["compressed_size"]]
        data = zlib.decompress(payload, -15) if header[3] == 8 else payload
        assert hashlib.sha256(data).hexdigest() == entry["sha256"]
        (root / kind / Path(entry["path"]).name).write_bytes(data)

repo = "https://raw.githubusercontent.com/nykemariotto/scratch-assay-segmentation"
revision = "6cbd78da604291a4b1dbf1926b06e44279381af3"
macro = "whst_batch.ijm"
for name, url, digest in [
    (
        macro,
        f"{repo}/{revision}/stage4/{macro}",
        "540a29fd80b371991fec5672a769fed689f8c2d81954806e113127eb82981da4",
    ),
    (
        "ij.jar",
        "https://repo.maven.apache.org/maven2/net/imagej/ij/1.54p/ij-1.54p.jar",
        "2e1a09961dfb41cee66ddc821b2577a41a072566ce45a49bae69267099741e20",
    ),
]:
    with urlopen(url, timeout=90) as response:
        data = response.read()
    assert hashlib.sha256(data).hexdigest() == digest
    (root / name).write_bytes(data)
source = (root / macro).read_text(encoding="utf-8")
for prompt, folder in [("Pasta com as imagens a medir", "images"), ("Onde salvar o CSV", "out")]:
    source = source.replace(f'getDirectory("{prompt}")', f'"{root.as_posix()}/{folder}/"')
(root / "batch.ijm").write_text(source, encoding="utf-8")
subprocess.run(
    [sys.argv[2], "-Xmx1g", "-cp", "ij.jar", "ij.ImageJ", "-batch", "batch.ijm"],
    cwd=root,
    check=True,
)
subprocess.run([sys.executable, Path(__file__).with_name("compare.py").resolve(), root], check=True)
