"""Budgeted ZIP members whose digest covers the bytes actually written."""

from collections.abc import Callable
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import BinaryIO
from zipfile import ZipFile


class ArchiveWriter:
    def __init__(self, archive: ZipFile, cancelled: Callable[[], bool]) -> None:
        self.archive = archive
        self.cancelled = cancelled
        self.members: list[dict[str, str | int]] = []
        self.total = 0

    def check_cancel(self) -> None:
        if self.cancelled():
            raise ValueError("项目归档已取消，未发布输出")

    def _write(
        self,
        name: str,
        stream: BinaryIO,
        role: str,
        expected_sha256: str = "",
        expected_size: int | None = None,
    ) -> None:
        self.check_cancel()
        if len(self.members) >= 4096 or any(m["path"] == name for m in self.members):
            raise ValueError("归档成员重复或超过4096个")
        if name.startswith("/") or ".." in name.split("/") or "\\" in name:
            raise ValueError("归档路径无效")
        digest, size = sha256(), 0
        with self.archive.open(name, "w", force_zip64=True) as member:
            while chunk := stream.read(1024 * 1024):
                self.check_cancel()
                size += len(chunk)
                self.total += len(chunk)
                if size > 512 * 1024 * 1024 or self.total > 2 * 1024**3:
                    raise ValueError("归档超过单文件512MiB或总计2GiB预算")
                member.write(chunk)
                digest.update(chunk)
        actual = digest.hexdigest()
        if expected_sha256 and actual != expected_sha256:
            raise ValueError("归档来源摘要不一致，文件已改变")
        if expected_size is not None and size != expected_size:
            raise ValueError("归档来源字节数不一致")
        self.members.append({"path": name, "sha256": actual, "size_bytes": size, "role": role})

    def data(self, name: str, data: bytes, role: str) -> None:
        self._write(name, BytesIO(data), role)

    def file(
        self,
        name: str,
        path: str | Path,
        role: str,
        expected_sha256: str = "",
        expected_size: int | None = None,
    ) -> None:
        with Path(path).open("rb") as stream:
            self._write(name, stream, role, expected_sha256, expected_size)
