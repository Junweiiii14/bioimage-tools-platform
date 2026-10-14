"""OCR text/layout suggestions and explicit measurement bindings; no recognition or I/O."""

import math
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TextBounds:
    x0: float
    y0: float
    x1: float
    y1: float

    def __post_init__(self) -> None:
        if any(not math.isfinite(value) for value in (self.x0, self.y0, self.x1, self.y1)):
            raise ValueError("OCR 坐标须有限")
        if self.x0 < 0 or self.y0 < 0 or self.x1 <= self.x0 or self.y1 <= self.y0:
            raise ValueError("OCR 坐标须为有效半开矩形")


@dataclass(frozen=True)
class TextToken:
    token_id: str
    text: str
    bounds: TextBounds
    confidence: float

    def __post_init__(self) -> None:
        if not self.token_id or not self.text.strip() or len(self.text) > 32767:
            raise ValueError("OCR 文字/身份无效")
        if not math.isfinite(self.confidence) or not 0 <= self.confidence <= 1:
            raise ValueError("OCR 置信度无效")


@dataclass(frozen=True)
class OCRRecognition:
    source_sha256: str
    width: int
    height: int
    tokens: tuple[TextToken, ...]
    engine_id: str
    model_hashes: tuple[tuple[str, str], ...]
    preprocess_id: str = "ocr_original_u8_or_u16_div257@1"
    schema_version: int = 1

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[0-9a-f]{64}", self.source_sha256):
            raise ValueError("OCR 来源须为 SHA256")
        if (
            type(self.width) is not int
            or type(self.height) is not int
            or min(self.width, self.height) <= 0
        ):
            raise ValueError("OCR 原始尺寸无效")
        if type(self.tokens) is not tuple or len({token.token_id for token in self.tokens}) != len(
            self.tokens
        ):
            raise ValueError("OCR token 身份须唯一且不可变")
        if any(
            token.bounds.x1 > self.width or token.bounds.y1 > self.height for token in self.tokens
        ):
            raise ValueError("OCR token 不得越出原图")


@dataclass(frozen=True)
class FigureSuggestion:
    figure_id: str
    heading: TextToken
    rows: tuple[TextToken, ...]
    bounds: TextBounds
    confirmed: bool = False


_FIGURE = re.compile(r"(?:fig(?:ure)?[ .-]*\d+[a-z]?|\d{1,3}[a-z])", re.IGNORECASE)


def _row_labels(tokens: tuple[TextToken, ...]) -> tuple[TextToken, ...]:
    """Suggest leading horizontal labels; retain aligned side-by-side panels, never rename text."""
    horizontal = tuple(
        token
        for token in tokens
        if token.bounds.x1 - token.bounds.x0 >= (token.bounds.y1 - token.bounds.y0) * 1.4
    )
    if not horizontal:
        return ()
    anchor = min(horizontal, key=lambda token: token.bounds.x0)
    tolerance = max(4.0, (anchor.bounds.y1 - anchor.bounds.y0) * 1.5)
    leading = tuple(
        token
        for token in horizontal
        if (
            token.bounds.x0 <= anchor.bounds.x0 + tolerance
            or abs(token.bounds.x1 - anchor.bounds.x1) <= tolerance
        )
    )
    return tuple(
        token
        for token in horizontal
        if token in leading
        or any(
            abs((token.bounds.y0 + token.bounds.y1 - row.bounds.y0 - row.bounds.y1) / 2)
            <= min(token.bounds.y1 - token.bounds.y0, row.bounds.y1 - row.bounds.y0) * 0.5
            for row in leading
        )
    )


def suggest_figures(recognition: OCRRecognition) -> tuple[FigureSuggestion, ...]:
    """Partition by explicit Fig heading tracks, then vertical intervals. No protein guessing."""
    headings = sorted(
        (token for token in recognition.tokens if _FIGURE.fullmatch(token.text.strip())),
        key=lambda token: (token.bounds.x0, token.bounds.y0),
    )
    tracks: list[list[TextToken]] = []
    for heading in headings:
        if not tracks or heading.bounds.x0 - tracks[-1][0].bounds.x0 > recognition.width * 0.10:
            tracks.append([])
        tracks[-1].append(heading)
    anchors = [track[0].bounds.x0 for track in tracks]
    boundaries = [
        0.0,
        *(anchor - anchors[0] for anchor in anchors[1:]),
        float(recognition.width),
    ]
    groups: list[FigureSuggestion] = []
    for column, track in enumerate(tracks):
        track.sort(key=lambda token: token.bounds.y0)
        left, right = boundaries[column : column + 2]
        for index, heading in enumerate(track):
            top = heading.bounds.y0
            bottom = (
                track[index + 1].bounds.y0 if index + 1 < len(track) else float(recognition.height)
            )
            rows = tuple(
                sorted(
                    (
                        token
                        for token in recognition.tokens
                        if token not in headings
                        and left <= (token.bounds.x0 + token.bounds.x1) / 2 < right
                        and top < (token.bounds.y0 + token.bounds.y1) / 2 < bottom
                    ),
                    key=lambda token: (token.bounds.y0, token.bounds.x0),
                )
            )
            groups.append(
                FigureSuggestion(
                    "F" + heading.token_id,
                    heading,
                    _row_labels(rows),
                    TextBounds(left, top, right, bottom),
                )
            )
    return tuple(groups)


@dataclass(frozen=True)
class MeasurementBinding:
    figure_id: str
    row_id: str
    column_id: str
    lane_id: str
    band_id: str

    def __post_init__(self) -> None:
        if not all((self.figure_id, self.row_id, self.column_id, self.lane_id, self.band_id)):
            raise ValueError("关联须有明确身份")


@dataclass(frozen=True)
class WorksheetRow:
    row_id: str
    figure_id: str
    figure_name: str
    row_name: str
    confirmed: bool

    def __post_init__(self) -> None:
        if not self.row_id or not self.figure_id or type(self.confirmed) is not bool:
            raise ValueError("行身份/确认状态无效")
        if self.confirmed and (not self.figure_name.strip() or not self.row_name.strip()):
            raise ValueError("确认行须有 Fig 名称和行名")


@dataclass(frozen=True)
class WorksheetColumn:
    column_id: str
    name: str

    def __post_init__(self) -> None:
        if not self.column_id or not self.name.strip():
            raise ValueError("结果列须有身份和名称")


@dataclass(frozen=True)
class Worksheet:
    source_sha256: str
    rows: tuple[WorksheetRow, ...]
    columns: tuple[WorksheetColumn, ...]
    bindings: tuple[MeasurementBinding, ...] = ()
    layout_id: str = "explicit_fig_row_lane_binding@1"

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[0-9a-f]{64}", self.source_sha256):
            raise ValueError("工作表须绑定原始测量来源")
        if any(type(value) is not tuple for value in (self.rows, self.columns, self.bindings)):
            raise ValueError("工作表须为不可变元组")
        if len({row.row_id for row in self.rows}) != len(self.rows):
            raise ValueError("工作表行身份重复")
        if len({column.column_id for column in self.columns}) != len(self.columns):
            raise ValueError("工作表列身份重复")
        rows = {row.row_id: row for row in self.rows}
        columns = {column.column_id for column in self.columns}
        seen: set[tuple[str, str]] = set()
        for binding in self.bindings:
            key = binding.row_id, binding.column_id
            if key in seen or binding.row_id not in rows or binding.column_id not in columns:
                raise ValueError("工作表绑定重复或身份不存在")
            if rows[binding.row_id].figure_id != binding.figure_id:
                raise ValueError("绑定不得跨 Fig")
            seen.add(key)
