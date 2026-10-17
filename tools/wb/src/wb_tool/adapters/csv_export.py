"""Versioned, reversible text encoding for spreadsheet-facing CSV reports."""

import csv
import math
from collections.abc import Callable
from io import StringIO
from pathlib import Path

from wb_tool.adapters.worksheet_export import Cell, publish_table_bytes

TEXT_PREFIX = "text:"
CSV_ENCODING = "wb_csv_text_prefix@1"


def csv_bytes(rows: tuple[tuple[Cell, ...], ...]) -> bytes:
    """Headers are controlled by this package; every data string has a literal prefix.

    Removing exactly one 'text:' recovers the original string, including empty strings.
    Numbers remain numbers and None is empty. Unlike quoting alone, labels cannot start
    with spreadsheet formula syntax, even when a viewer removes CSV quoting.
    """
    if not rows or sum(map(len, rows)) > 200000:
        raise ValueError("CSV表格为空或超出200000单元格预算")
    stream = StringIO(newline="")
    writer = csv.writer(stream, quoting=csv.QUOTE_NONNUMERIC, lineterminator="\r\n")
    writer.writerow(rows[0])
    for row in rows[1:]:
        if len(row) != len(rows[0]):
            raise ValueError("CSV列数不一致")
        encoded: list[Cell] = []
        for value in row:
            if isinstance(value, str):
                if len(value) > 32767 or any(ord(c) < 32 and c not in "\t\r\n" for c in value):
                    raise ValueError("CSV文字超限或含控制符")
                encoded.append(TEXT_PREFIX + value)
            elif value is None:
                encoded.append(None)
            elif isinstance(value, bool) or not math.isfinite(value):
                raise ValueError("CSV数值必须有限且不能为布尔值")
            else:
                encoded.append(value)
        writer.writerow(encoded)
        if stream.tell() > 32 * 1024 * 1024:
            raise ValueError("CSV超过32MiB文字预算")
    data = stream.getvalue().encode("utf-8-sig")
    if len(data) > 64 * 1024 * 1024:
        raise ValueError("CSV超过64MiB文件预算")
    return data


def publish_csv(
    rows: tuple[tuple[Cell, ...], ...],
    destination: str | Path,
    *,
    cancelled: Callable[[], bool] = lambda: False,
) -> Path:
    return publish_table_bytes(csv_bytes(rows), destination, ".csv", cancelled=cancelled)
