"""Run the author's CLI on fixed flask scans and compare with same-ID coordinates."""

import csv
import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw
from softagar.engine import detect_colonies
from softagar.io import load_image

archive, output = map(Path, sys.argv[1:])
with archive.open("rb") as stream:
    if hashlib.file_digest(stream, "md5").hexdigest() != "1d45b5a3bd7c50c80e628ab4cb664445":
        raise ValueError("Zenodo archive digest mismatch")
output.mkdir(parents=True, exist_ok=False)
ids = [f"T47D-0412-C{i}" for i in (1, 2, 3)]
with zipfile.ZipFile(archive) as files:
    for sample in ids:
        for folder in ["ColonyImages", "GT", "MCC_Observer1", "MCC_Observer2", "MCC_Observer3"]:
            suffix = "tif" if folder == "ColonyImages" else "txt"
            files.extract(f"Dataset1_T47D/{folder}/{sample}.{suffix}", output)

dataset = output / "Dataset1_T47D"
counts = output / "counts.csv"
subprocess.run(
    [sys.executable, "-m", "softagar.cli", "count", "-i", dataset / "ColonyImages", "-o", counts],
    check=True,
)
with counts.open(newline="") as stream:
    cli = {Path(row["filename"]).stem: int(row["count"]) for row in csv.DictReader(stream)}
if set(cli) != set(ids):
    raise ValueError("Unexpected flask IDs")

for sample in ids:
    path = dataset / "ColonyImages" / f"{sample}.tif"
    with Image.open(path) as raw:
        assert raw.tag_v2[258] == (16, 16, 16)
    rgb = load_image(path)
    result = detect_colonies(rgb)
    assert result["count"] == cli[sample]
    gt = np.loadtxt(dataset / "GT" / f"{sample}.txt")
    observers = [len(np.loadtxt(dataset / f"MCC_Observer{i}" / f"{sample}.txt")) for i in (1, 2, 3)]
    overlay = Image.fromarray(rgb)
    draw = ImageDraw.Draw(overlay)
    for spot in result["colonies"]:
        x, y, r = (spot[k] for k in ("x", "y", "radius"))
        draw.ellipse((x - r, y - r, x + r, y + r), outline="lime", width=3)
    for x, y in gt:
        draw.line((x - 8, y, x + 8, y), fill="magenta", width=3)
        draw.line((x, y - 8, x, y + 8), fill="magenta", width=3)
    overlay.save(output / f"{sample}-overlay.png")

    # Audit the engine's delivered candidate mask against its own strict area gate.
    contours, _ = cv2.findContours(result["mask"], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(
        sample,
        "CLI / GT / observers / delta:",
        cli[sample],
        len(gt),
        observers,
        cli[sample] - len(gt),
    )
    with (output / f"{sample}-contours.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["x", "y", "w", "h", "area_px2", "accepted", "gt_points_inside"])
        for contour in contours:
            area = cv2.contourArea(contour)
            inside = sum(cv2.pointPolygonTest(contour, tuple(point), False) >= 0 for point in gt)
            writer.writerow([*cv2.boundingRect(contour), area, 525 < area < 15000, inside])
