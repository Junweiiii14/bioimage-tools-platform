"""Read a bounded literal subset of XLSX / UTF-8 CSV. Never evaluate workbook content."""

import csv
import io
import posixpath
import re
from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZIP_STORED, BadZipFile, ZipFile
from zlib import error as ZlibError

from wb_tool.application.project_metadata import MetadataBook, MetadataCell, MetadataSheet

_S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
_P = "{http://schemas.openxmlformats.org/package/2006/relationships}"
_LIMIT = 16 * 1024 * 1024


def _cell(text: str, error: str = "") -> MetadataCell:
    if len(text) > 2000:
        raise ValueError("单元格超过 2000 字符预算")
    return MetadataCell(text, error)


def _coordinate(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"([A-Z]{1,3})([1-9][0-9]{0,6})", value)
    if match is None:
        raise ValueError("Excel 单元格坐标无效")
    col = 0
    for letter in match[1]:
        col = col * 26 + ord(letter) - 64
    row = int(match[2])
    if row > 1025 or col > 64:
        raise ValueError("元信息工作表超过 1025 行 / 64 列预算，请另存元信息区域")
    return row - 1, col - 1


def _rich_text(element: ET.Element) -> str:
    # Do not include phonetic guides (rPh) in identifiers.
    return "".join(
        child.text or "" for child in element.findall(f"{_S}t") + element.findall(f"{_S}r/{_S}t")
    )


def _sheet(
    root: ET.Element, name: str, shared: tuple[str, ...], cancelled: Callable[[], bool]
) -> MetadataSheet:
    if root.tag != f"{_S}worksheet":
        raise ValueError("不支持此 Excel 工作表格式")
    values: dict[tuple[int, int], MetadataCell] = {}
    ranges: list[tuple[str, str]] = []
    for node in root.findall(f"{_S}sheetData/{_S}row/{_S}c"):
        if len(values) % 256 == 0 and cancelled():
            raise ValueError("元信息导入已取消")
        coord = _coordinate(node.get("r", ""))
        if coord in values:
            raise ValueError("Excel 单元格坐标重复")
        kind = node.get("t", "n")
        text = node.findtext(f"{_S}v", "")
        error = ""
        formula = node.find(f"{_S}f")
        if formula is not None:
            text, error = "", "公式不可导入（不使用缓存值）"
            if formula.get("ref"):
                ranges.append((formula.get("ref", ""), error))
        elif kind == "s":
            if not text.isdecimal() or not 0 <= int(text) < len(shared):
                raise ValueError("Excel 共享字符串索引无效")
            text = shared[int(text)]
        elif kind == "inlineStr":
            inline = node.find(f"{_S}is")
            text = _rich_text(inline) if inline is not None else ""
        elif kind not in ("n", "str"):
            text, error = "", "日期、布尔值或错误单元格不可作为元信息"
        values[coord] = _cell(text, error)
    for merge in root.findall(f"{_S}mergeCells/{_S}mergeCell"):
        ranges.append((merge.get("ref", ""), "合并单元格请拆分后填写"))
    expanded = 0
    for reference, error in ranges:
        ends = reference.split(":")
        if len(ends) not in (1, 2):
            raise ValueError("Excel 区域无效")
        top, left = _coordinate(ends[0])
        bottom, right = _coordinate(ends[-1])
        if bottom < top or right < left:
            raise ValueError("Excel 区域方向无效")
        expanded += (bottom - top + 1) * (right - left + 1)
        if expanded > 65536:
            raise ValueError("Excel 合并 / 公式区域累计超过 65536 单元格预算")
        for r in range(top, bottom + 1):
            if cancelled():
                raise ValueError("元信息导入已取消")
            for c in range(left, right + 1):
                values[r, c] = MetadataCell(
                    values.get((r, c), MetadataCell()).text if "合并" in error else "", error
                )
    height = max((r + 1 for r, _ in values), default=0)
    width = max((c + 1 for _, c in values), default=0)
    return MetadataSheet(
        name,
        tuple(
            tuple(values.get((r, c), MetadataCell()) for c in range(width)) for r in range(height)
        ),
    )


def _xlsx(data: bytes, cancelled: Callable[[], bool]) -> tuple[MetadataSheet, ...]:
    with ZipFile(io.BytesIO(data)) as archive:
        entries = archive.infolist()
        names = {entry.filename for entry in entries}
        if len(entries) > 2048 or len(names) != len(entries):
            raise ValueError("Excel 包重复或超过 2048 成员预算")
        if any(
            e.compress_type not in (ZIP_STORED, ZIP_DEFLATED) or e.flag_bits & 1 for e in entries
        ):
            raise ValueError("不支持加密或特殊压缩 Excel")
        if any(
            "vba" in n.lower() or "activex" in n.lower() or "externallinks/" in n.lower()
            for n in names
        ):
            raise ValueError("请另存不含宏、活动控件或外部链接的元信息表")

        xml_bytes = 0

        def xml(name: str) -> ET.Element:
            nonlocal xml_bytes
            if cancelled():
                raise ValueError("元信息导入已取消")
            if name not in names or archive.getinfo(name).file_size > _LIMIT:
                raise ValueError("Excel 部件缺失或超过 16 MiB 预算")
            xml_bytes += archive.getinfo(name).file_size
            if xml_bytes > 32 * 1024 * 1024:
                raise ValueError("Excel 元信息 XML 总计超过 32 MiB 解压预算")
            with archive.open(name) as stream:
                raw = stream.read(_LIMIT + 1)
            if len(raw) > _LIMIT:
                raise ValueError("Excel 部件超过预算")
            # Accept UTF-8 OOXML only; block DTD/entity declarations before parsing.
            decoded = raw.decode("utf-8-sig")
            if "<!DOCTYPE" in decoded.upper() or "<!ENTITY" in decoded.upper() or "\x00" in decoded:
                raise ValueError("Excel XML 声明不受支持")
            return ET.fromstring(decoded)

        workbook = xml("xl/workbook.xml")
        if workbook.tag != f"{_S}workbook":
            raise ValueError("仅支持普通 .xlsx 工作簿")
        rels: dict[str, str] = {}
        shared_path = ""
        for rel in xml("xl/_rels/workbook.xml.rels").findall(f"{_P}Relationship"):
            kind = rel.get("Type", "").rsplit("/", 1)[-1]
            if kind not in ("worksheet", "sharedStrings"):
                continue
            target = rel.get("Target", "")
            resolved = (
                posixpath.normpath("xl/" + target) if not target.startswith("/") else target[1:]
            )
            if (
                rel.get("TargetMode") == "External"
                or not resolved.startswith("xl/")
                or "\\" in target
                or ":" in target
            ):
                raise ValueError("Excel 工作表关系路径无效")
            identity = rel.get("Id", "")
            if not identity or identity in rels:
                raise ValueError("Excel 关系身份重复或缺失")
            rels[identity] = resolved
            if kind == "sharedStrings":
                if shared_path:
                    raise ValueError("Excel 共享字符串表重复")
                shared_path = resolved
        shared = (
            tuple(_rich_text(item) for item in xml(shared_path).findall(f"{_S}si"))
            if shared_path
            else ()
        )
        if len(shared) > 65536 or any(len(value) > 2000 for value in shared):
            raise ValueError("Excel 共享文字超出预算")
        sheets = workbook.findall(f"{_S}sheets/{_S}sheet")
        if not 1 <= len(sheets) <= 16:
            raise ValueError("元信息工作簿须为 1–16 张工作表")
        result: list[MetadataSheet] = []
        total = 0
        for sheet in sheets:
            path = rels.get(sheet.get(f"{_R}id", ""), "")
            parsed = _sheet(xml(path), sheet.get("name", "未命名"), shared, cancelled)
            total += sum(len(row) for row in parsed.rows)
            if total > 65536:
                raise ValueError("元信息总计超过 65536 单元格预算")
            result.append(parsed)
        return tuple(result)


def read_metadata_file(
    path: str | Path, *, cancelled: Callable[[], bool] = lambda: False
) -> MetadataBook:
    source = Path(path)
    if source.suffix.lower() not in (".xlsx", ".csv"):
        raise ValueError("请选择 .xlsx 或 UTF-8 CSV 元信息表")
    with source.open("rb") as stream:
        data = stream.read(_LIMIT + 1)
    if len(data) > _LIMIT:
        raise ValueError("元信息表超过 16 MiB 预算")
    if cancelled():
        raise ValueError("元信息导入已取消")
    try:
        if source.suffix.lower() == ".xlsx":
            sheets = _xlsx(data, cancelled)
        else:
            rows: list[tuple[MetadataCell, ...]] = []
            total = 0
            for values in csv.reader(
                io.StringIO(data.decode("utf-8-sig"), newline=""), strict=True
            ):
                if cancelled():
                    raise ValueError("元信息导入已取消")
                total += len(values)
                if len(rows) >= 1025 or len(values) > 64 or total > 65536:
                    raise ValueError("CSV 超过 1025 行 / 64 列 / 65536 单元格预算")
                rows.append(
                    tuple(
                        _cell(value, "公式不可导入" if value.lstrip().startswith("=") else "")
                        for value in values
                    )
                )
            width = max(map(len, rows), default=0)
            sheets = (
                MetadataSheet(
                    source.stem, tuple(row + (MetadataCell(),) * (width - len(row)) for row in rows)
                ),
            )
    except (
        BadZipFile,
        ET.ParseError,
        UnicodeError,
        csv.Error,
        NotImplementedError,
        RuntimeError,
        EOFError,
        ZlibError,
    ) as error:
        raise ValueError(f"无法读取元信息表：{error}") from error
    if cancelled():
        raise ValueError("元信息导入已取消")
    return MetadataBook(sha256(data).hexdigest(), sheets)
