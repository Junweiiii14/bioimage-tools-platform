"""Literal source labels for automatic composition, never biological pairing."""

import re
from dataclasses import dataclass
from pathlib import PurePosixPath

_FIG_FOLDER = re.compile(r"(?:fig(?:ure)?[ ._-]*)?([1-9]\d{0,3}[a-z]?)", re.IGNORECASE)
_FIG_FILE = re.compile(r"fig(?:ure)?[ ._-]*([1-9]\d{0,3}[a-z]?)(?=$|[ ._-])", re.IGNORECASE)
_ACQUISITION = re.compile(r"(.+?)_\d{6}_\d+_\d+_\d+_\d+(?:\s*\(\d+\))?$", re.IGNORECASE)
_NUMBERED_ACQUISITION = re.compile(r"(.+?_\d{6}_\d+_\d+_\d+_\d+)\s*\((\d+)\)$", re.IGNORECASE)


@dataclass(frozen=True)
class SourceImportLabels:
    figure: str | None
    protein: str | None
    policy: str = "literal_source_labels@1"


def source_import_labels(source: str) -> SourceImportLabels:
    """Read an explicit Fig folder/file label and acquisition filename prefix.

    Both separators are supported so labels survive Windows project fixtures on
    Linux. Only the immediate parent is considered: an experiment's ancestors
    do not silently group unrelated subfolders. Conflicting explicit labels stay
    unassigned. Protein text is a literal label, not an identity or control claim.
    """
    path = PurePosixPath(source.replace("\\", "/"))
    folder = _FIG_FOLDER.fullmatch(path.parent.name)
    filename = _FIG_FILE.match(path.stem)
    folder_label = folder.group(1).upper() if folder else None
    file_label = filename.group(1).upper() if filename else None
    figure = (
        None
        if folder_label and file_label and folder_label != file_label
        else file_label or folder_label
    )
    acquisition = _ACQUISITION.fullmatch(path.stem)
    protein = acquisition.group(1).strip() if acquisition else None
    if protein and filename:
        protein = protein[filename.end() :].lstrip(" ._-") or None
    if protein and (len(protein) > 120 or "\n" in protein or "\r" in protein):
        protein = None
    return SourceImportLabels(figure, protein)


def preferred_acquisition_sources(paths: tuple[str, ...]) -> tuple[str, ...]:
    """Prefer an unnumbered acquisition or (1) among same-directory numbered copies.

    Only the explicit acquisition timestamp/settings pattern qualifies. Different
    acquisition settings, ordinary filenames and groups without a primary remain
    untouched. This is a folder-import policy; explicit file imports remain available.
    No file is deleted or rewritten.
    """
    available = {str(PurePosixPath(path.replace("\\", "/"))) for path in paths}
    selected: list[str] = []
    for source in paths:
        path = PurePosixPath(source.replace("\\", "/"))
        numbered = _NUMBERED_ACQUISITION.fullmatch(path.stem)
        if numbered:
            base, number = numbered.groups()
            primary = path.with_name(base + path.suffix)
            first = path.with_name(base + " (1)" + path.suffix)
            if str(primary) in available or (int(number) > 1 and str(first) in available):
                continue
        selected.append(source)
    return tuple(selected)
