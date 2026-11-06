"""One external CSV/record boundary; no inference of missing experimental facts."""

import csv
import hashlib
import io
import math
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from bca_tool.domain.plate import LEVELS, Well

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=512)]


class PlateRecord(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    method_id: Literal["pierce25-point-v0-research"]
    kit: Literal["23225", "23227", "A65453"]
    sop: Literal["MAN0011430 Rev D"]
    sample_volume_ul: Literal[25]
    working_reagent_ul: Literal[200]
    reagent_a_to_b: Literal["50:1"]
    mixing_seconds: Literal[30]
    incubation_c: Literal[37]
    incubation_minutes: Literal[30]
    wavelength_nm: Literal[562]
    cooled_to_room_temperature: Literal[True]
    diluent: Text
    same_diluent_for_all_wells: Literal[True]
    same_treatment_for_all_wells: Literal[True]
    matrix_compatibility_basis: Text
    instrument: Text
    read_date: date
    reading_kind: Literal["raw_absorbance"]
    source_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


@dataclass(frozen=True)
class PlateInput:
    wells: tuple[Well, ...]
    record: PlateRecord
    csv_bytes: bytes
    record_bytes: bytes


COLUMNS = tuple(Well.__dataclass_fields__)


def read_plate(source_path: str, record_path: str) -> PlateInput:
    raw, record_raw = Path(source_path).read_bytes(), Path(record_path).read_bytes()
    record = PlateRecord.model_validate_json(record_raw)
    if hashlib.sha256(raw).hexdigest() != record.source_sha256:
        raise ValueError("source_digest: CSV differs from explicit plate record")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
    if reader.fieldnames != list(COLUMNS):
        raise ValueError("csv_columns: expected exact ordered long-CSV columns")
    wells: list[Well] = []
    positions: set[str] = set()
    repeats: set[tuple[str, str, str]] = set()
    identities: dict[str, tuple[str, float | None, float]] = {}
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise ValueError("csv_row: missing or extra cells")
        plate, well, role, sample, repeat = (row[k] for k in COLUMNS[:5])
        if not all(s and s.strip() == s for s in (plate, well, sample, repeat)):
            raise ValueError("identity: explicit nonempty identifiers required")
        if not re.fullmatch(r"[A-H](?:[1-9]|1[0-2])", well) or well in positions:
            raise ValueError("well: invalid or duplicate 96-well position")
        if role not in ("blank", "standard", "sample"):
            raise ValueError("role: expected blank, standard or sample")
        key = (role, sample, repeat)
        if key in repeats:
            raise ValueError("identity: duplicate technical replicate")
        absorbance, dilution = float(row["a562"]), float(row["dilution_factor"])
        concentration = float(row["standard_ug_ml"]) if row["standard_ug_ml"] else None
        if not all(math.isfinite(v) for v in (absorbance, dilution)) or dilution < 1:
            raise ValueError("numeric: finite readings and dilution >=1 required")
        if role == "sample":
            if concentration is not None:
                raise ValueError("sample: standard concentration must be empty")
        elif dilution != 1 or concentration not in (LEVELS[:1] if role == "blank" else LEVELS[1:]):
            raise ValueError("standard: fixed BSA levels, blank zero and dilution 1 required")
        identity = (role, concentration, dilution)
        if sample in identities and identities[sample] != identity:
            raise ValueError("identity: role, standard level or dilution differs within sample")
        identities[sample] = identity
        positions.add(well)
        repeats.add(key)
        wells.append(Well(plate, well, role, sample, repeat, absorbance, concentration, dilution))
    if len({w.plate_id for w in wells}) != 1:
        raise ValueError("plate: exactly one nonempty plate required")
    for concentration in LEVELS:
        group = [w for w in wells if w.role != "sample" and w.standard_ug_ml == concentration]
        if len(group) < 2 or len({w.sample_id for w in group}) != 1:
            raise ValueError(
                "standards: every fixed level needs one identity and >=2 technical wells"
            )
    samples = {w.sample_id for w in wells if w.role == "sample"}
    if not samples or any(sum(w.sample_id == s for w in wells) < 2 for s in samples):
        raise ValueError("samples: each explicit sample requires >=2 technical wells")
    return PlateInput(tuple(wells), record, raw, record_raw)
