"""Bounded ZIP reads with generated staging names; never use archive extraction paths."""

import re
import stat
import struct
from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import BinaryIO
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

MAX_TOTAL = 2 * 1024**3
MAX_MEMBER = 512 * 1024**2
MAX_CONTAINER = MAX_TOTAL + 8 * 1024**2
_NAME = re.compile(
    r"(?:archive\.json|manifest\.json|project\.json|figure\.png|README\.txt|"
    r"assets/[0-9a-f]{64}|crops/[0-9]{4}\.tif|"
    r"runs/[0-9]{4}/(?:run|request|result)\.json|"
    r"tables/(?:source|ocr|normalization|normalization_ocr)\.(?:csv|xlsx))"
)


def check_cancel(cancelled: Callable[[], bool]) -> None:
    if cancelled():
        raise ValueError("项目恢复已取消")


def preflight_zip(stream: BinaryIO, size: int, *, max_members: int = 4096) -> int:
    """Bound central-directory allocation before constructing Python's ZipFile."""
    if size < 22 or size > MAX_CONTAINER:
        raise ValueError("ZIP容器超出大小预算")
    stream.seek(0)
    if stream.read(4) != b"PK\x03\x04":
        raise ValueError("不支持带前缀或空ZIP")
    start = max(0, size - 65557)
    stream.seek(start)
    tail = stream.read(65557)
    offset = tail.rfind(b"PK\x05\x06")
    if offset < 0 or len(tail) - offset < 22:
        raise ValueError("ZIP缺少完整目录结尾")
    _, disk, central_disk, count_disk, count, length, position, comment = struct.unpack(
        "<4s4H2LH", tail[offset : offset + 22]
    )
    end = start + offset
    if offset + 22 + comment != len(tail) or disk or central_disk or count_disk != count:
        raise ValueError("ZIP分卷/结尾/计数无效")
    stream.seek(max(0, end - 20))
    locator = stream.read(20)
    if locator[:4] == b"PK\x06\x07":
        _, disk64, location, disks = struct.unpack("<4sLQL", locator)
        if disk64 or disks != 1 or location + 56 != end - 20:
            raise ValueError("ZIP64目录结构无效")
        stream.seek(location)
        header = stream.read(56)
        if len(header) != 56:
            raise ValueError("ZIP64目录截断")
        sig, record_size, _, _, d1, d2, n1, n2, length, position = struct.unpack(
            "<4sQ2H2L4Q", header
        )
        if sig != b"PK\x06\x06" or record_size != 44 or d1 or d2 or n1 != n2:
            raise ValueError("ZIP64目录字段无效")
        count, end = n2, location
    if not 0 < count <= max_members or length > 4 * 1024**2 or position + length != end:
        raise ValueError("ZIP成员数/中央目录超出预算或位置无效")
    stream.seek(0)
    return count


@dataclass(frozen=True)
class ArchiveEntry:
    name: str
    path: Path
    sha256: str
    size_bytes: int


def snapshot_archive(source: Path, destination: Path, cancelled: Callable[[], bool]) -> str:
    digest, size = sha256(), 0
    with source.open("rb") as original, destination.open("xb") as copied:
        while chunk := original.read(1024 * 1024):
            check_cancel(cancelled)
            size += len(chunk)
            if size > MAX_CONTAINER:
                raise ValueError("ZIP容器超出大小预算")
            copied.write(chunk)
            digest.update(chunk)
    return digest.hexdigest()


def read_archive(
    path: Path, staging: Path, cancelled: Callable[[], bool]
) -> dict[str, ArchiveEntry]:
    entries: dict[str, ArchiveEntry] = {}
    with path.open("rb") as stream:
        count = preflight_zip(stream, path.stat().st_size)
        with ZipFile(stream) as archive:
            infos = archive.infolist()
            if len(infos) != count or sum(info.file_size for info in infos) > MAX_TOTAL:
                raise ValueError("ZIP目录计数/解压总量超出预算")
            names: set[str] = set()
            for info in infos:
                name = info.filename
                if (
                    not _NAME.fullmatch(name)
                    or name != info.orig_filename
                    or name in names
                    or info.flag_bits & (1 | 64)
                    or info.external_attr & 0x10
                    or info.volume != 0
                    or info.compress_type not in (ZIP_STORED, ZIP_DEFLATED)
                    or stat.S_IFMT(info.external_attr >> 16) not in (0, stat.S_IFREG)
                ):
                    raise ValueError("ZIP含非法/重复/加密/链接成员或未知压缩格式")
                names.add(name)
                limit = MAX_TOTAL if name.startswith("assets/") else MAX_MEMBER
                if name.endswith(".json"):
                    limit = 16 * 1024**2
                elif name.endswith((".png", ".csv", ".xlsx")):
                    limit = 64 * 1024**2
                elif name == "README.txt":
                    limit = 64 * 1024
                if info.file_size > limit:
                    raise ValueError("ZIP成员超过读取预算")
            for number, info in enumerate(infos):
                check_cancel(cancelled)
                # Names from the archive are never used to form a filesystem path.
                target = staging / f"entry-{number:04d}.bin"
                digest, size = sha256(), 0
                with archive.open(info) as member, target.open("xb") as output:
                    while chunk := member.read(1024 * 1024):
                        check_cancel(cancelled)
                        size += len(chunk)
                        if size > info.file_size:
                            raise ValueError("ZIP成员实际长度超过声明")
                        output.write(chunk)
                        digest.update(chunk)
                if size != info.file_size:
                    raise ValueError("ZIP成员长度不一致")
                entries[info.filename] = ArchiveEntry(
                    info.filename, target, digest.hexdigest(), size
                )
    return entries
