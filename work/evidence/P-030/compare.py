"""Compare an ImageJ batch run to the four archived YOLO polygons."""

import csv
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

root = Path(sys.argv[1])
manifest = json.loads(Path(__file__).with_name("manifest.json").read_text())
rows = []
panels = []
for frame in manifest:
    image = Path(frame["arquivo_b"])
    original = Image.open(root / "images" / image)
    w, h = original.size
    reference = np.zeros((h, w), np.uint8)
    label = root / "labels" / image.with_suffix(".txt")
    for line in label.read_text().splitlines():
        category, *vertices = line.split()
        assert category == "0"
        points = np.array(vertices, dtype=float).reshape(-1, 2)
        assert ((points >= 0) & (points <= 1)).all()
        contour = np.rint(points * [w, h]).astype(np.int32)
        cv2.fillPoly(reference, [contour], 1)
    mask = np.asarray(Image.open(root / "out/masks" / (image.stem + "_mask.png"))) > 0
    assert mask.shape == reference.shape
    predicted_px, reference_px = int(mask.sum()), int(reference.sum())
    if not rows:
        initial, baseline = predicted_px, reference_px
    predicted_closure = 100 * (1 - predicted_px / initial)
    reference_closure = 100 * (1 - reference_px / baseline)
    iou = np.logical_and(reference, mask).sum() / np.logical_or(reference, mask).sum()
    rows.append(
        [
            frame["timepoint_h"],
            predicted_px,
            reference_px,
            round(iou, 4),
            round(predicted_closure, 3),
            round(reference_closure, 3),
            round(predicted_closure - reference_closure, 3),
        ]
    )
    canvas = np.array(original.convert("RGB"))
    for bitmap, color in [(mask.astype(np.uint8), (0, 210, 255)), (reference, (255, 155, 0))]:
        outlines, _ = cv2.findContours(bitmap, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(canvas, outlines, -1, color, 7)
    panels.append(Image.fromarray(canvas).resize((490, 411), Image.Resampling.LANCZOS))
writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(
    [
        "hour",
        "method_px2",
        "reference_px2",
        "gap_iou",
        "method_closure_pct",
        "reference_closure_pct",
        "difference_pp",
    ]
)
writer.writerows(rows)
sheet = Image.new("RGB", (980, 878), "white")
draw = ImageDraw.Draw(sheet)
for index, panel in enumerate(panels):
    x, y = (index % 2) * 490, (index // 2) * 439
    draw.text((x + 4, y + 5), f"{rows[index][0]} h  |  IoU {rows[index][3]:.3f}", fill="black")
    sheet.paste(panel, (x, y + 27))
sheet.save(root / "contours.jpg", quality=88)
