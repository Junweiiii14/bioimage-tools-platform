"""Fig-sheet geometry proposals. Detection copies never supply quantitative values."""

import re
from collections import Counter
from dataclasses import dataclass, replace
from math import ceil
from typing import cast

import numpy as np
from numpy.typing import NDArray

from wb_tool.domain.lanes import LaneROI
from wb_tool.domain.scipy_geometry import filters
from wb_tool.domain.worksheet import OCRRecognition, TextToken

FIG_HEADING = re.compile(r"fig(?:ure)?[ .-]*(\d+)[ .-]*([a-z])?", re.IGNORECASE)


@dataclass(frozen=True)
class SheetRowProposal:
    figure: str
    protein: str
    crop: LaneROI
    lanes: tuple[LaneROI, ...]
    warnings: tuple[str, ...]


def framed_blocks(pixels: NDArray[np.uint8 | np.uint16]) -> tuple[LaneROI, ...]:
    """Find filled rectangular blot regions on a light page, at bounded resolution."""
    step = max(1, ceil(max(pixels.shape) / 2048))
    small = pixels[::step, ::step]
    maximum = np.iinfo(pixels.dtype).max
    mask = small < maximum * 0.94
    components, _ = filters.label(mask)
    boxes: list[LaneROI] = []
    for index, bounds in enumerate(filters.find_objects(components), 1):
        if bounds is None:
            continue
        ys, xs = bounds
        top, bottom, left, right = (
            cast(int, value) for value in (ys.start, ys.stop, xs.start, xs.stop)
        )
        height, width = bottom - top, right - left
        if width < 24 or height < 7 or width * height < 260:
            continue
        if np.count_nonzero(components[ys, xs] == index) / (width * height) < 0.55:
            continue
        # Work in original coordinates, with a small inset to exclude frame ink.
        inset = max(2, step)
        x0, y0 = left * step + inset, top * step + inset
        x1 = min(pixels.shape[1], right * step) - inset
        y1 = min(pixels.shape[0], bottom * step) - inset
        if x1 > x0 and y1 > y0:
            boxes.append(LaneROI(f"block-{index}", x0, y0, x1, y1))
    return tuple(boxes)


def block_lanes(pixels: NDArray[np.uint8 | np.uint16], box: LaneROI) -> tuple[LaneROI, ...]:
    local = pixels[box.y0 : box.y1, box.x0 : box.x1].astype(np.float64)
    height = local.shape[0]
    residual = np.maximum(0, np.percentile(local, 85, axis=1)[:, None] - local)
    signal = filters.gaussian_filter(residual, sigma=1.5)
    if float(signal.max()) < max(2, np.iinfo(pixels.dtype).max * 0.004):
        return ()
    components, _ = filters.label(signal > float(signal.max()) * 0.2)
    spans: list[tuple[int, int]] = []
    for i, region in enumerate(filters.find_objects(components), 1):
        if region is None:
            continue
        ys, xs = region
        left, right, top, bottom = (cast(int, v) for v in (xs.start, xs.stop, ys.start, ys.stop))
        area = int(np.count_nonzero(components[region] == i))
        if (
            right - left >= height * 0.25
            and bottom - top >= height * 0.06
            and area >= height * height * 0.025
        ):
            spans.append((left, right))
    if not spans:
        return ()
    typical = float(np.percentile([b - a for a, b in spans], 75))
    merged: list[tuple[int, int]] = []
    for a, b in sorted(spans):
        if (
            merged
            and a - merged[-1][1] < typical * 0.4
            and max(b, merged[-1][1]) - merged[-1][0] <= typical * 1.5
        ):
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else:
            merged.append((a, b))
    centers = [(a + b) // 2 for a, b in merged]
    if len(centers) > 96:
        return ()
    cuts = [0, *[(a + b) // 2 for a, b in zip(centers, centers[1:], strict=False)], box.width]
    return tuple(
        LaneROI(f"lane-{i}", box.x0 + a, box.y0, box.x0 + b, box.y1)
        for i, (a, b) in enumerate(zip(cuts, cuts[1:], strict=False), 1)
    )


def sheet_lane_pitch(blocks: tuple[LaneROI, ...]) -> float | None:
    """Common cell-width suggestion from at least three distinct frame widths.

    A single repeated width cannot distinguish 2 lanes from 4 and is refused.
    """
    widths: list[list[int]] = []
    for width in sorted(b.width for b in blocks):
        if not widths or width - float(np.median(widths[-1])) > 8:
            widths.append([])
        widths[-1].append(width)
    values = np.array([float(np.median(group)) for group in widths])
    if len(values) < 3:
        return None
    candidates: list[tuple[float, float, float]] = []
    for width in values:
        for count in range(1, 33):
            pitch = float(width / count)
            if pitch < max(8, float(values.min()) / 16):
                continue
            ratios = values / pitch
            errors = np.abs(ratios - np.rint(ratios))
            supported = (errors <= 0.06) & (ratios >= 0.95) & (ratios <= 96.05)
            if int(supported.sum()) >= 3 and float(supported.mean()) >= 0.8:
                candidates.append(
                    (float(supported.mean()), float(np.median(errors[supported])), pitch)
                )
    if not candidates:
        return None
    support = max(c[0] for c in candidates)
    best_error = min(c[1] for c in candidates if c[0] == support)
    return max(c[2] for c in candidates if c[0] == support and c[1] <= best_error + 0.01)


def partition_sheet(
    pixels: NDArray[np.uint8 | np.uint16], recognition: OCRRecognition
) -> tuple[SheetRowProposal, ...]:
    if pixels.shape != (recognition.height, recognition.width):
        raise ValueError("Fig识别尺寸与原图不符")
    headings = [t for t in recognition.tokens if FIG_HEADING.fullmatch(t.text.strip())]
    if not headings:
        raise ValueError("未识别到Fig标签，请使用手动分组")
    blocks = framed_blocks(pixels)
    pitch = sheet_lane_pitch(blocks)
    assigned: dict[str, list[LaneROI]] = {t.token_id: [] for t in headings}
    tracks: list[list[TextToken]] = []
    for heading in sorted(headings, key=lambda t: t.bounds.x0):
        if not tracks or heading.bounds.x0 - tracks[-1][0].bounds.x0 > recognition.width * 0.045:
            tracks.append([])
        tracks[-1].append(heading)
    for box in blocks:
        eligible = [
            track
            for track in tracks
            if min(t.bounds.x0 for t in track) <= box.x0 + 16
            and any(t.bounds.y0 <= (box.y0 + box.y1) / 2 + 16 for t in track)
        ]
        candidates = (
            [t for t in eligible[-1] if t.bounds.y0 <= (box.y0 + box.y1) / 2 + 16]
            if eligible
            else []
        )
        if candidates:
            heading = max(candidates, key=lambda t: t.bounds.y0)
            row_labels = sorted(
                (
                    t
                    for t in recognition.tokens
                    if t not in headings
                    and heading.bounds.x0 <= t.bounds.x0 < box.x0
                    and box.y0 <= (t.bounds.y0 + t.bounds.y1) / 2 <= box.y1
                ),
                key=lambda t: t.bounds.y0,
            )
            centers: list[int] = []
            for t in row_labels:
                center = round((t.bounds.y0 + t.bounds.y1) / 2)
                if not centers or center - centers[-1] > max(12, t.bounds.y1 - t.bounds.y0):
                    centers.append(center)
            cuts = [
                box.y0,
                *[(a + b) // 2 for a, b in zip(centers, centers[1:], strict=False)],
                box.y1,
            ]
            assigned[heading.token_id].extend(
                replace(box, y0=a, y1=b) for a, b in zip(cuts, cuts[1:], strict=False) if b - a >= 2
            )
    rows: list[SheetRowProposal] = []
    for heading in sorted(headings, key=lambda t: (t.bounds.x0, t.bounds.y0)):
        match = FIG_HEADING.fullmatch(heading.text.strip())
        assert match is not None
        figure = "Fig" + match[1] + (match[2] or "").upper()
        lines: list[list[LaneROI]] = []
        for box in sorted(assigned[heading.token_id], key=lambda b: (b.y0, b.x0)):
            if (
                lines
                and abs((box.y0 + box.y1) / 2 - (lines[-1][0].y0 + lines[-1][0].y1) / 2)
                < min(box.y1 - box.y0, lines[-1][0].y1 - lines[-1][0].y0) * 0.5
            ):
                lines[-1].append(box)
            else:
                lines.append([box])
        for number, line in enumerate(lines, 1):
            line.sort(key=lambda b: b.x0)
            box = line[0]
            labels: list[TextToken] = [
                t
                for t in recognition.tokens
                if t not in headings
                and heading.bounds.x0 <= t.bounds.x0 < box.x0
                and abs((t.bounds.y0 + t.bounds.y1) / 2 - (box.y0 + box.y1) / 2)
                < (box.y1 - box.y0) * 0.55
            ]
            text = (
                min(labels, key=lambda t: box.x0 - t.bounds.x1).text if labels else f"条带 {number}"
            )
            local_segments = tuple(block_lanes(pixels, segment) for segment in line)
            lanes = tuple(lane for segment in local_segments for lane in segment)
            local_lanes = lanes
            flags = ("fig_partition@1", "automatic_labels_and_lanes_unreviewed")
            if pitch is not None and all(
                abs(segment.width / pitch - round(segment.width / pitch)) <= 0.06
                for segment in line
            ):
                lanes = tuple(
                    LaneROI(
                        f"slot-{i}",
                        segment.x0 + round(i * segment.width / count),
                        segment.y0,
                        segment.x0 + round((i + 1) * segment.width / count),
                        segment.y1,
                    )
                    for segment in line
                    for count in (max(1, round(segment.width / pitch)),)
                    for i in range(count)
                )
                flags += ("repeated_frame_width_lattice@1;check_lane_count",)
                counts = {len(segment) for segment in local_segments}
                if len(line) > 1 and len(counts) == 1 and next(iter(counts)) >= 2:
                    lanes = local_lanes
                    flags += ("segmented_signal_consensus@1",)
            if (match[2] or "").upper() in {"I", "L"}:
                flags += ("ambiguous_fig_suffix_I_L;check_original_heading",)
            if not labels:
                flags += ("missing_protein_label",)
            if not lanes or len(lanes) > 96:
                lanes = ()
                flags += ("lane_detection_unavailable",)
            crop = LaneROI(
                "proposal",
                min(b.x0 for b in line),
                min(b.y0 for b in line),
                max(b.x1 for b in line),
                max(b.y1 for b in line),
            )
            rows.append(SheetRowProposal(figure, text[:120], crop, lanes, flags))
    if not rows or len(rows) > 512:
        raise ValueError("没有可分组条带或超过512行预算，请手动分组")
    # Only transfer a lane layout across equal-width aligned rows when at least two
    # rows independently agree. A weak/missing lane remains a slot, never a zero.
    corrected: list[SheetRowProposal] = []
    for item in rows:
        peers = [
            r
            for r in rows
            if r.figure == item.figure
            and abs(r.crop.x0 - item.crop.x0) <= 8
            and abs(r.crop.x1 - item.crop.x1) <= 8
            and r.lanes
        ]
        counts = Counter(len(r.lanes) for r in peers)
        if counts:
            count, votes = counts.most_common(1)[0]
            if votes >= 2 and len(item.lanes) != count:
                witness = next(r for r in peers if len(r.lanes) == count)
                lanes = tuple(
                    replace(
                        lane,
                        y0=item.crop.y0,
                        y1=item.crop.y1,
                        x0=max(item.crop.x0, lane.x0),
                        x1=min(item.crop.x1, lane.x1),
                    )
                    for lane in witness.lanes
                )
                item = replace(
                    item,
                    lanes=lanes,
                    warnings=(*item.warnings, "cross_row_lane_layout_suggestion@1"),
                )
        corrected.append(item)
    return tuple(
        sorted(corrected, key=lambda r: (int(re.sub(r"\D", "", r.figure)), r.figure, r.crop.y0))
    )
