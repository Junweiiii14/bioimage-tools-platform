"""Probe the one exploratory TIFF from IOCBIO Additional file 1 (local ZIP argument)."""

import hashlib
import sys
import tempfile
import zipfile
from pathlib import Path

import tifffile
from wb_tool.api import CropDetectionSettings, load_tiff, suggest_crops

archive = Path(sys.argv[1])
if hashlib.sha256(archive.read_bytes()).hexdigest() != (
    "66c84b4a5557ccfd203bec15becbc9e85ca7c681e9e2b2545f24092b60059c46"
):
    raise ValueError("Unexpected archive")
with zipfile.ZipFile(archive) as z, tempfile.TemporaryDirectory() as tmp:
    name = "gel1_GAPDH_expo1min.tif"
    path = Path(tmp) / name
    path.write_bytes(z.read("gel_images/" + name))
    image = load_tiff(path)
    with tifffile.TiffFile(path) as tif:
        print(len(tif.pages), tif.pages[0].tags["Model"].value)
    pixels = image.pixels
    print(image.sha256, image.photometric, image.conversion, pixels.shape, pixels.dtype)
    print(pixels.min(), pixels.max(), (pixels == 0).sum(), (pixels == 65535).sum())
    # Exploratory settings only; lane count and marker are not experimental identities.
    proposal = suggest_crops(
        str(path), image.sha256, "gel1-gapdh", 0, CropDetectionSettings(13, 30, "light")
    )
    if proposal.result is None:
        print(proposal.error)
    else:
        print(proposal.result.algorithm_id, proposal.result.flags, len(proposal.result.candidates))
