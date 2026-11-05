"""Fetch the exact public P014 inputs into a new or matching external cache."""

import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path
from urllib.request import urlopen


def fetch(url, destination, expected):
    if destination.exists():
        data = destination.read_bytes()
    else:
        with urlopen(url, timeout=120) as response:
            data = response.read(100_000_001)
        if len(data) > 100_000_000:
            raise ValueError("Unexpected resource size")
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Hash mismatch: {destination.name}")
    if not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(data)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    evidence = Path(__file__).parent
    base = "https://ftp.ebi.ac.uk/biostudies/fire/S-BIAD/634/S-BIAD634/Files/"
    for filename in ["development-downloads.json", "evaluation-downloads.json"]:
        records = json.loads((evidence / filename).read_text(encoding="utf-8"))
        for record in records:
            url = record["url"]
            if not url.startswith(base):
                raise ValueError("Unexpected data host")
            relative = Path(url.removeprefix(base))
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Unsafe data path")
            fetch(url, args.root / relative, record["sha256"])
    config = json.loads((evidence / "frozen-config.json").read_text(encoding="utf-8"))
    url = "https://github.com/stardist/stardist-models/releases/download/v0.1/"
    name = "python_2D_versatile_fluo.zip"
    data = fetch(url + name, args.root / name, config["model_archive_sha256"])
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for name, expected in config["model_files_sha256"].items():
            if name not in ("config.json", "thresholds.json", "weights_best.h5"):
                raise ValueError("Unexpected model member")
            data = archive.read(name)
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError("Model member hash mismatch")
            path = args.root / "models" / "2D_versatile_fluo" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                if path.read_bytes() != data:
                    raise ValueError("Existing model differs; refusing overwrite")
            else:
                with path.open("xb") as stream:
                    stream.write(data)
    print("All public inputs verified")


if __name__ == "__main__":
    main()
