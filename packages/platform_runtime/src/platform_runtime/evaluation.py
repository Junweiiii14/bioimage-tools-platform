"""Deterministic evidence comparison; never issues a scientific approval."""

from hashlib import sha256
from math import isfinite

from tool_contracts.api import (
    MethodEvaluationEvidence,
    MethodEvaluationPlan,
    MethodEvaluationReport,
    ValidationComparison,
    ValidationDataRecord,
)


def method_plan_digest(plan: MethodEvaluationPlan) -> str:
    plan = MethodEvaluationPlan.model_validate(plan.model_dump(mode="python"))
    return sha256(plan.model_dump_json().encode("utf-8")).hexdigest()


def dataset_partition_issues(records: tuple[ValidationDataRecord, ...]) -> tuple[str, ...]:
    """Resolve parent closure so derivatives cannot cross the holdout boundary."""
    records = tuple(
        ValidationDataRecord.model_validate(x.model_dump(mode="python")) for x in records
    )
    by_id = {x.record_id: x for x in records}
    if len(by_id) != len(records):
        return ("duplicate_data_identity",)
    issues: set[str] = set()
    resolved: dict[str, set[str]] = {}

    def groups(record_id: str, active: frozenset[str]) -> set[str]:
        if record_id in active:
            issues.add("dataset_lineage_cycle")
            return set()
        if record_id in resolved:
            return resolved[record_id]
        record = by_id.get(record_id)
        if record is None:
            issues.add("missing_parent_record")
            return set()
        result = set(record.source_groups)
        for parent in record.parent_record_ids:
            result.update(groups(parent, active | {record_id}))
        if not result and record.partition != "unassigned":
            issues.add("unknown_source_group:" + record_id)
        resolved[record_id] = result
        return result

    development: set[str] = set()
    heldout: set[str] = set()
    for record in records:
        lineage = groups(record.record_id, frozenset())
        if record.partition == "development":
            development.update(lineage)
        elif record.partition == "holdout":
            heldout.update(lineage)
    if development & heldout:
        issues.add("source_group_leakage")
    return tuple(sorted(issues))


def evaluate_method(
    plan: MethodEvaluationPlan, evidence: MethodEvaluationEvidence
) -> MethodEvaluationReport:
    """Compare frozen references and exact attempt identity, including missing values."""
    # Revalidate Python values before serializing: the JSON serializer may coerce
    # a bool injected via model_copy into a float, or turn NaN into null.
    plan = MethodEvaluationPlan.model_validate(plan.model_dump(mode="python"))
    evidence = MethodEvaluationEvidence.model_validate(evidence.model_dump(mode="python"))
    digest = method_plan_digest(plan)
    issues = list(dataset_partition_issues(plan.records))
    if evidence.plan_sha256 != digest:
        issues.append("frozen_plan_mismatch")
    if evidence.module != plan.module:
        issues.append("method_implementation_mismatch")
    if evidence.environment != plan.environment:
        issues.append("runtime_environment_mismatch")
    observed = {x.case_id: x for x in evidence.observations}
    if set(observed) - {x.case_id for x in plan.cases}:
        issues.append("undeclared_observation")
    records = {x.record_id: x for x in plan.records}
    comparisons: list[ValidationComparison] = []
    for case in plan.cases:
        record = records[case.record_id]
        actual = observed.get(case.case_id)
        reasons: list[str] = []
        error = None
        if (
            record.file_status != "verified_local"
            or record.decode_status != "decoded"
            or record.license_use_status != "allowed"
            or record.evidence_kind == "catalog_reference"
        ):
            reasons.append("data_not_admitted_for_evaluation")
        if record.unit != case.unit:
            reasons.append("reference_unit_mismatch")
        if actual is None:
            reasons.append("missing_observation")
        else:
            if actual.payload_sha256 != record.payload_sha256:
                reasons.append("input_digest_mismatch")
            if actual.parameters_sha256 != case.parameters_sha256:
                reasons.append("parameters_mismatch")
            if actual.unit != case.unit:
                reasons.append("observation_unit_mismatch")
            if actual.status != case.expected_status:
                reasons.append("measurement_state_mismatch")
            if case.expected_status == "valid":
                if case.expected_value is None or case.absolute_tolerance is None:
                    reasons.append("missing_frozen_reference_or_tolerance")
                elif actual.value is not None:
                    error = abs(actual.value - case.expected_value)
                    if not isfinite(error):
                        error = None
                        reasons.append("numeric_difference_overflow")
                    elif error > case.absolute_tolerance:
                        reasons.append("outside_frozen_tolerance")
        comparisons.append(
            ValidationComparison(
                case_id=case.case_id,
                expected_status=case.expected_status,
                actual_status=actual.status if actual else None,
                expected_value=case.expected_value,
                actual_value=actual.value if actual else None,
                absolute_error=error,
                passed=not reasons,
                reasons=tuple(reasons),
            )
        )
    passed = not issues and all(x.passed for x in comparisons)
    # Arithmetic agreement does not authenticate independent data, a reviewer,
    # applicability, or an approval. S1 is deliberately a separate task/record.
    reasons = [*issues, "scientific_admission_requires_separate_review"]
    if not any(
        x.partition == "holdout" and x.evidence_kind == "independent_reference"
        for x in plan.records
    ):
        reasons.append("no_independent_holdout_reference")
    return MethodEvaluationReport(
        evaluation_id=plan.evaluation_id,
        plan_sha256=digest,
        evidence_sha256=sha256(evidence.model_dump_json().encode("utf-8")).hexdigest(),
        comparisons=tuple(comparisons),
        engineering_passed=passed,
        requested_use_allowed=passed and plan.intended_use == "engineering",
        reasons=tuple(reasons),
    )
