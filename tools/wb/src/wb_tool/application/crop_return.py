"""Outcome of a verified, non-replacing source-folder crop publication."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReturnedCrop:
    row_id: str
    revision: int
    files: tuple[str, ...]
    receipt: str
