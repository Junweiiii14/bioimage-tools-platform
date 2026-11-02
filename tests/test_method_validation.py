"""Evidence identity, lineage closure, missing values and real analytical use cases."""

import json
from hashlib import sha256
from pathlib import Path
from typing import Literal

import pytest
from hypothesis import example, given
from hypothesis import strategies as st
from platform_runtime.api import dataset_partition_issues, evaluate_method, method_plan_digest
from pydantic import ValidationError
from tool_contracts.api import (
    MethodEvaluationEvidence,
    MethodEvaluationPlan,
    MethodObservation,
    ModulePort,
    ModuleSpec,
    RuntimeVersion,
    ValidationCase,
    ValidationDataRecord,
)

from tooling.wb_method_validation import ROOT, run_wb_validation


def data_record(
    record_id: str = "source",
    *,
    partition: Literal["development", "holdout", "unassigned"] = "development",
    groups: tuple[str, ...] = ("acquisition_A",),
    parents: tuple[str, ...] = (),
) -> ValidationDataRecord:
    return ValidationDataRecord(
        record_id=record_id,
        dataset_id="analytic_v1",
        source_groups=groups,
        parent_record_ids=parents,
        partition=partition,
        evidence_kind="synthetic_analytic",
        payload_sha256="a" * 64,
        file_status="verified_local",
        decode_status="decoded",
        license_use_status="allowed",
        license_and_use="Self-generated arithmetic example",
        unit="example_unit",
    )


def evaluation_pair(value: float = 0.0) -> tuple[MethodEvaluationPlan, MethodEvaluationEvidence]:
    module = ModuleSpec(
        module_id="test_calculation",
        module_version="1",
        method_version="arithmetic@1",
        implementation_digest="b" * 64,
        input_ports=(ModulePort(name="source", kind="raw_image"),),
        output_ports=(ModulePort(name="table", kind="typed_table", filename="table.json"),),
        parameters_schema="{}",
    )
    plan = MethodEvaluationPlan(
        evaluation_id="reference_1",
        intended_use="engineering",
        module=module,
        environment=(RuntimeVersion(name="fixture", version="1"),),
        records=(data_record(),),
        cases=(
            ValidationCase(
                case_id="case_1",
                record_id="source",
                metric_id="value",
                unit="example_unit",
                parameters_sha256="c" * 64,
                expected_status="valid",
                expected_value=value,
                absolute_tolerance=0.0,
                reference_source="Frozen arithmetic reference, independent of implementation",
            ),
        ),
    )
    evidence = MethodEvaluationEvidence(
        plan_sha256=method_plan_digest(plan),
        module=module,
        environment=plan.environment,
        observations=(
            MethodObservation(
                case_id="case_1",
                payload_sha256="a" * 64,
                parameters_sha256="c" * 64,
                unit="example_unit",
                status="valid",
                value=value,
            ),
        ),
    )
    return plan, evidence


@given(value=st.floats(min_value=-1e9, max_value=1e9, allow_nan=False, allow_infinity=False))
@example(value=0.0)
def test_perfect_synthetic_agreement_never_issues_scientific_approval(value: float) -> None:
    plan, evidence = evaluation_pair(value)
    engineering = evaluate_method(plan, evidence)
    assert engineering.engineering_passed and engineering.requested_use_allowed
    scientific = plan.model_copy(update={"intended_use": "scientific"})
    matched = evidence.model_copy(update={"plan_sha256": method_plan_digest(scientific)})
    report = evaluate_method(scientific, matched)
    assert report.engineering_passed
    assert not report.requested_use_allowed
    assert report.scientific_admission == "not_granted"
    assert "no_independent_holdout_reference" in report.reasons


@given(depth=st.integers(min_value=1, max_value=40), reverse=st.booleans())
def test_derivative_parent_closure_cannot_hide_holdout_leakage(depth: int, reverse: bool) -> None:
    records = [data_record("root")]
    for index in range(depth):
        records.append(
            data_record(
                f"derived_{index}",
                partition="holdout" if index == depth - 1 else "unassigned",
                groups=(),
                parents=("root" if index == 0 else f"derived_{index - 1}",),
            )
        )
    if reverse:
        records.reverse()
    assert "source_group_leakage" in dataset_partition_issues(tuple(records))


@pytest.mark.parametrize("change", ["input", "parameters", "unit", "implementation", "environment"])
def test_changed_attempt_identity_cannot_pass(change: str) -> None:
    plan, evidence = evaluation_pair()
    actual = evidence.observations[0]
    if change == "implementation":
        evidence = evidence.model_copy(
            update={
                "module": evidence.module.model_copy(update={"implementation_digest": "d" * 64})
            }
        )
    elif change == "environment":
        evidence = evidence.model_copy(
            update={"environment": (RuntimeVersion(name="fixture", version="2"),)}
        )
    else:
        key, value = {
            "input": ("payload_sha256", "d" * 64),
            "parameters": ("parameters_sha256", "d" * 64),
            "unit": ("unit", "different_unit"),
        }[change]
        evidence = evidence.model_copy(
            update={"observations": (actual.model_copy(update={key: value}),)}
        )
    assert not evaluate_method(plan, evidence).requested_use_allowed


def test_missing_references_observations_and_zero_are_distinct() -> None:
    plan, evidence = evaluation_pair()
    assert evaluate_method(plan, evidence).comparisons[0].actual_value == 0.0
    missing = evaluate_method(plan, evidence.model_copy(update={"observations": ()}))
    assert not missing.engineering_passed
    assert missing.comparisons[0].actual_value is None
    assert missing.comparisons[0].absolute_error is None
    unknown = plan.model_copy(
        update={"cases": (plan.cases[0].model_copy(update={"absolute_tolerance": None}),)}
    )
    matched = evidence.model_copy(update={"plan_sha256": method_plan_digest(unknown)})
    assert not evaluate_method(unknown, matched).requested_use_allowed
    # Editing a frozen reference without new execution evidence cannot repair a failed run.
    changed = plan.model_copy(
        update={"cases": (plan.cases[0].model_copy(update={"expected_value": 8.0}),)}
    )
    assert "frozen_plan_mismatch" in evaluate_method(changed, evidence).reasons


def test_unknown_lineage_missing_parent_cycle_and_catalog_are_not_admission() -> None:
    assert dataset_partition_issues((data_record(groups=()),)) == ("unknown_source_group:source",)
    assert "missing_parent_record" in dataset_partition_issues((data_record(parents=("absent",)),))
    assert "dataset_lineage_cycle" in dataset_partition_issues((data_record(parents=("source",)),))
    plan, evidence = evaluation_pair()
    cited = plan.records[0].model_copy(update={"evidence_kind": "catalog_reference"})
    plan = plan.model_copy(update={"records": (cited,)})
    evidence = evidence.model_copy(update={"plan_sha256": method_plan_digest(plan)})
    assert not evaluate_method(plan, evidence).engineering_passed


def test_nonfinite_values_and_false_validity_are_rejected_at_public_boundary() -> None:
    plan, evidence = evaluation_pair()
    for value in (float("nan"), float("inf"), True, None):
        observation = evidence.observations[0].model_copy(update={"value": value})
        with pytest.raises(ValidationError):
            evaluate_method(plan, evidence.model_copy(update={"observations": (observation,)}))
    huge = plan.model_copy(
        update={"cases": (plan.cases[0].model_copy(update={"expected_value": -1e308}),)}
    )
    evidence = evidence.model_copy(
        update={
            "plan_sha256": method_plan_digest(huge),
            "observations": (evidence.observations[0].model_copy(update={"value": 1e308}),),
        }
    )
    report = evaluate_method(huge, evidence)
    assert not report.engineering_passed
    assert report.comparisons[0].absolute_error is None


def test_real_analytic_wb_report_preserves_expectations_sources_and_invalid_nulls(
    tmp_path: Path,
) -> None:
    output = tmp_path / "evaluation"
    report = run_wb_validation(output)
    assert report.engineering_passed and report.requested_use_allowed
    readiness = json.loads((output / "method-register.json").read_text(encoding="utf-8"))
    assert (
        readiness[0]["engineering_report_sha256"]
        == sha256((output / "report.json").read_bytes()).hexdigest()
    )
    assert readiness[0]["design_readiness"] == "ready"
    assert readiness[1]["design_readiness"] == "pending"
    assert readiness[1]["implementation_digest"] is None
    assert all(x["scientific_admission"] == "not_granted" for x in readiness)
    assert [x.actual_value for x in report.comparisons] == [40.0, 4000.0, 0.0, None, None]
    assert [x.absolute_error for x in report.comparisons] == [0.0, 0.0, 0.0, None, None]
    assert report.scientific_admission == "not_granted"
    source = json.loads(
        (ROOT / "work/evidence/B-007/public-development-data.json").read_text(encoding="utf-8")
    )
    catalog = json.loads((output / "source-catalog.json").read_text(encoding="utf-8"))
    assert [json.loads(x["source_record_json"]) for x in catalog["records"]] == source["records"]
    assert all(x["payload_sha256"] is None for x in catalog["records"])
    original = (output / "report.json").read_bytes()
    with pytest.raises(FileExistsError):
        run_wb_validation(output)
    assert (output / "report.json").read_bytes() == original


def test_scientific_request_keeps_numerical_report_but_denies_admission(tmp_path: Path) -> None:
    report = run_wb_validation(tmp_path / "candidate", intended_use="scientific")
    assert report.engineering_passed and not report.requested_use_allowed


def test_changed_frozen_source_definition_is_not_silently_ignored(tmp_path: Path) -> None:
    path = ROOT / "work/evidence/P-001/frozen-case-design.json"
    design = json.loads(path.read_text(encoding="utf-8"))
    design["cases"][0]["profile"][1] = 999
    changed = tmp_path / "reference.json"
    changed.write_text(json.dumps(design), encoding="utf-8")
    with pytest.raises(ValueError, match="source definition"):
        run_wb_validation(tmp_path / "rejected", design_path=changed)
    assert not (tmp_path / "rejected/report.json").exists()
