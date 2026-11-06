"""Analytical P018 expectations through the real external boundary."""

import csv
import hashlib
import io
import json
from pathlib import Path

import pytest
from bca_tool.api import analyze_plate, read_plate

EXAMPLES = Path(__file__).parents[1] / "examples"


def changed_input(tmp_path: Path, row: int, field: str, value: str) -> tuple[str, str]:
    rows = list(csv.DictReader((EXAMPLES / "synthetic.csv").open(encoding="utf-8")))
    rows[row][field] = value
    text = io.StringIO(newline="")
    writer = csv.DictWriter(text, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    raw = text.getvalue().encode()
    source = tmp_path / "input.csv"
    source.write_bytes(raw)
    record = json.loads((EXAMPLES / "record.json").read_text())
    record["source_sha256"] = hashlib.sha256(raw).hexdigest()
    metadata = tmp_path / "record.json"
    metadata.write_text(json.dumps(record))
    return str(source), str(metadata)


def test_hand_calculated_wells_then_technical_summary() -> None:
    plate = read_plate(str(EXAMPLES / "synthetic.csv"), str(EXAMPLES / "record.json"))
    result = analyze_plate(plate.wells)
    s1 = result.samples[0]
    # Hand piecewise inverse: 250+(0.37-0.20)/0.18*250 and 500+0.01/0.16*250.
    assert [r.assayed_ug_ml for r in result.wells[18:20]] == pytest.approx(
        [486.1111111111111, 515.625], abs=1e-10
    )
    assert s1.mean_original_ug_ml == pytest.approx(5008.680555555556, abs=1e-10)
    assert s1.sd_original_ug_ml == pytest.approx(208.69470972519616, abs=1e-10)
    assert (s1.n_total, s1.n_valid) == (2, 2)
    assert s1.mean_original_ug_ml != 5000  # Averaging absorbance first changes the answer.
    assert result.wells[20].status == "below_supported_range"
    assert result.wells[21].status == "above_supported_range"
    assert result.wells[22].assayed_ug_ml is None
    partial = result.samples[-1]
    assert (partial.n_total, partial.n_valid, partial.status) == (2, 1, "partial")
    assert partial.mean_original_ug_ml is partial.sd_original_ug_ml is None
    assert all(r.assayed_ug_ml is None for r in result.wells[:18])


@pytest.mark.parametrize(
    ("row", "field", "value"),
    [
        (1, "well", "A1"),
        (19, "technical_replicate", "1"),
        (18, "sample_id", ""),
        (18, "a562", "NaN"),
        (18, "a562", "OVER"),
        (18, "a562", ""),
        (18, "dilution_factor", "0"),
        (19, "dilution_factor", "2"),
        (2, "standard_ug_ml", "20"),
        (0, "role", "standard"),
        (18, "standard_ug_ml", "0"),
        (18, "plate_id", "another"),
        (18, "sample_id", "single"),
    ],
)
def test_external_invalid_inputs(tmp_path: Path, row: int, field: str, value: str) -> None:
    with pytest.raises(ValueError):
        read_plate(*changed_input(tmp_path, row, field, value))


def test_nonmonotonic_curve_fails_whole_plate(tmp_path: Path) -> None:
    plate = read_plate(*changed_input(tmp_path, 2, "a562", "3"))
    with pytest.raises(ValueError, match="invalid_curve"):
        analyze_plate(plate.wells)


def test_unknown_record_and_stale_digest_are_rejected(tmp_path: Path) -> None:
    metadata = tmp_path / "record.json"
    record = json.loads((EXAMPLES / "record.json").read_text())
    for field, value in (
        ("same_treatment_for_all_wells", False),
        ("sample_volume_ul", 10),
        ("matrix_compatibility_basis", ""),
        ("source_sha256", "0" * 64),
    ):
        metadata.write_text(json.dumps({**record, field: value}))
        with pytest.raises(ValueError):
            read_plate(str(EXAMPLES / "synthetic.csv"), str(metadata))


def test_supported_endpoints_and_valid_zero_remains_low(tmp_path: Path) -> None:
    for absorbance, expected in (("0.07", 25.0), ("1.13", 2000.0), ("0.05", None)):
        result = analyze_plate(read_plate(*changed_input(tmp_path, 18, "a562", absorbance)).wells)
        if expected is None:
            assert result.wells[18].assayed_ug_ml is None
        else:
            assert result.wells[18].assayed_ug_ml == pytest.approx(expected, abs=1e-10)
