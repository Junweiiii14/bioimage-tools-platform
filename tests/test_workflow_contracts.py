"""Finite graph, scientific roles and frozen identity, independently of any GUI/worker."""

import hashlib
import json
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st
from platform_runtime.api import (
    ModuleRegistration,
    WorkflowValidationError,
    compile_workflow,
    execution_plan_digest,
    load_execution_plan,
    load_workflow_definition,
    verify_execution_plan,
    workflow_definition_json,
)
from pydantic import BaseModel, ConfigDict, ValidationError
from tool_contracts.api import (
    AssetRef,
    CoordinateFrame,
    ExecutionPlan,
    ImageMetadata,
    ModulePort,
    ModuleSpec,
    NodePosition,
    PortTypeBinding,
    RuntimeVersion,
    ScientificAsset,
    ScientificPort,
    ScientificType,
    SeriesMetadata,
    TableColumn,
    TableMetadata,
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowInput,
    WorkflowLayout,
    WorkflowModule,
    WorkflowNode,
    WorkflowOutput,
    canonical_module_json,
)

from tooling.wb_workflow_plan import freeze_wb_plan, wb_plan_registration

ENV = (RuntimeVersion(name="fixture", version="1"),)


class Parameters(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)
    gain: int


def source() -> ScientificAsset:
    return ScientificAsset(
        payload=AssetRef(
            asset_id="original", relative_path="input.tif", sha256="a" * 64, size_bytes=10
        ),
        sample_id="sample",
        description=ScientificType(
            kind="raw_image",
            unit="detector_count",
            image=ImageMetadata(
                dtype="uint16",
                axes=("y", "x"),
                shape=(5, 3),
                acquisition_bit_depth=None,
                acquisition_range=None,
                acquisition_range_source=None,
                frame=CoordinateFrame(
                    frame_id="original_pixels",
                    origin_asset_sha256="a" * 64,
                    physical_pixel_size_yx=None,
                    physical_unit=None,
                ),
            ),
        ),
        producing_method=None,
        parameters_sha256=None,
    )


def registration() -> ModuleRegistration:
    schema = canonical_module_json(json.dumps(Parameters.model_json_schema()))
    module = ModuleSpec(
        module_id="contract_fixture",
        module_version="1",
        method_version="no_execution@1",
        implementation_digest="b" * 64,
        parameters_schema=schema,
        input_ports=(ModulePort(name="source", kind="raw_image"),),
        output_ports=(ModulePort(name="result", kind="raw_image", filename="result.tif"),),
    )
    interface = WorkflowModule(
        module=module,
        input_ports=(
            ScientificPort(
                name="source",
                kind="raw_image",
                quantitative=True,
                accepted_dtypes=("uint16",),
                unit="detector_count",
                frame_id="original_pixels",
                frame_origin_sha256="a" * 64,
            ),
        ),
        output_ports=(PortTypeBinding(port="result", description=source().description),),
    )

    def validate(raw: str) -> None:
        Parameters.model_validate_json(raw, strict=True)

    return ModuleRegistration(
        interface=interface, parameters_schema=schema, validate_parameters=validate
    )


def graph() -> WorkflowDefinition:
    module = registration().interface.module
    return WorkflowDefinition(
        workflow_id="workflow",
        workflow_version="1",
        revision=0,
        title="Fixture",
        sample_id="sample",
        nodes=tuple(
            WorkflowNode(
                node_id=name,
                module=module,
                parameters_json=json.dumps({"gain": 9 if name == "C" else 1}),
            )
            for name in ("A", "B", "C")
        ),
        edges=(
            WorkflowEdge(
                source_node="A", source_port="result", target_node="B", target_port="source"
            ),
        ),
        inputs=tuple(
            WorkflowInput(node_id=name, port="source", asset=source()) for name in ("A", "C")
        ),
        outputs=(
            WorkflowOutput(name="main", node_id="B", port="result"),
            WorkflowOutput(name="independent", node_id="C", port="result"),
        ),
    )


def compile_fixture(definition: WorkflowDefinition) -> ExecutionPlan:
    return compile_workflow(definition, (registration(),), ENV)


def test_fixed_graph_json_roundtrip_and_plan_reopen() -> None:
    definition = graph()
    restored = load_workflow_definition(workflow_definition_json(definition))
    assert restored == definition
    plan = compile_fixture(restored)
    assert [n.node_id for n in plan.nodes] == ["A", "C", "B"]
    assert plan.nodes[-1].inputs[0].source_key == plan.nodes[0].computation_key
    assert load_execution_plan(plan.model_dump_json(), (registration(),)) == plan
    assert execution_plan_digest(plan) == execution_plan_digest(
        verify_execution_plan(plan, (registration(),))
    )


@given(st.permutations((0, 1, 2)), st.permutations((0, 1)))
def test_definition_order_and_layout_never_change_computation_keys(
    order: tuple[int, ...], inputs: tuple[int, ...]
) -> None:
    original = graph()
    plan = compile_fixture(original)
    moved = original.model_copy(
        update={
            "nodes": tuple(original.nodes[i] for i in order),
            "inputs": tuple(original.inputs[i] for i in inputs),
            "revision": 20,
            "title": "Renamed",
        }
    )
    after = compile_fixture(moved)
    assert {n.node_id: n.computation_key for n in plan.nodes} == {
        n.node_id: n.computation_key for n in after.nodes
    }
    layout = WorkflowLayout(positions=(NodePosition(node_id="A", x=20.0, y=30.0),), zoom=2.0)
    assert "positions" in layout.model_dump_json() and "positions" not in plan.model_dump_json()


@given(st.integers(min_value=-10000, max_value=10000).filter(lambda x: x != 1))
def test_parameter_change_invalidates_exactly_descendants(value: int) -> None:
    original = graph()
    before = compile_fixture(original)
    changed = original.nodes[0].model_copy(update={"parameters_json": json.dumps({"gain": value})})
    after = compile_fixture(original.model_copy(update={"nodes": (changed, *original.nodes[1:])}))
    old = {n.node_id: n.computation_key for n in before.nodes}
    new = {n.node_id: n.computation_key for n in after.nodes}
    assert old["A"] != new["A"] and old["B"] != new["B"] and old["C"] == new["C"]


@pytest.mark.parametrize(
    "change,expected",
    [
        ("cycle", "cycle"),
        ("missing", "missing_input"),
        ("duplicate_node", "duplicate_node"),
        ("duplicate_binding", "duplicate_binding"),
        ("unknown_node", "unknown_node"),
        ("unknown_port", "unknown_output_port"),
        ("module_version", "unknown_module"),
        ("implementation", "module_mismatch"),
        ("method", "module_mismatch"),
        ("parameters", "parameters"),
        ("extra_parameters", "parameters"),
        ("sample", "sample_mismatch"),
        ("unit", "unit"),
        ("frame", "coordinate_frame"),
        ("display", "display_into_quantitation"),
    ],
)
def test_preflight_rejects_bad_graphs_with_reasons(change: str, expected: str) -> None:
    d = graph()
    nodes = list(d.nodes)
    edges = d.edges
    inputs = list(d.inputs)
    if change == "cycle":
        edges += (
            WorkflowEdge(
                source_node="B", source_port="result", target_node="A", target_port="source"
            ),
        )
    elif change == "missing":
        edges = ()
    elif change == "duplicate_node":
        nodes.append(nodes[0])
    elif change == "duplicate_binding":
        inputs.append(inputs[0])
    elif change == "unknown_node":
        edges = (edges[0].model_copy(update={"source_node": "absent"}),)
    elif change == "unknown_port":
        edges = (edges[0].model_copy(update={"source_port": "absent"}),)
    elif change in ("module_version", "implementation", "method"):
        field = {
            "module_version": "module_version",
            "implementation": "implementation_digest",
            "method": "method_version",
        }[change]
        nodes[0] = nodes[0].model_copy(
            update={
                "module": nodes[0].module.model_copy(
                    update={field: "c" * 64 if change == "implementation" else "unknown"}
                )
            }
        )
    elif change in ("parameters", "extra_parameters"):
        nodes[0] = nodes[0].model_copy(
            update={
                "parameters_json": "{}" if change == "parameters" else '{"gain":1,"surprise":true}'
            }
        )
    else:
        asset = inputs[0].asset
        desc = asset.description
        if change == "sample":
            asset = asset.model_copy(update={"sample_id": "other"})
        elif change == "unit":
            asset = asset.model_copy(
                update={"description": desc.model_copy(update={"unit": "concentration"})}
            )
        elif change == "frame":
            assert desc.image is not None
            asset = asset.model_copy(
                update={
                    "description": desc.model_copy(
                        update={
                            "image": desc.image.model_copy(
                                update={
                                    "frame": desc.image.frame.model_copy(
                                        update={"frame_id": "other_frame"}
                                    )
                                }
                            )
                        }
                    )
                }
            )
        elif change == "display":
            assert desc.image is not None
            asset = asset.model_copy(
                update={
                    "description": desc.model_copy(
                        update={
                            "kind": "display_image",
                            "image": desc.image.model_copy(update={"dtype": "uint8"}),
                        }
                    ),
                    "parent_payloads": (
                        AssetRef(
                            asset_id="parent",
                            relative_path="parent.tif",
                            sha256="c" * 64,
                            size_bytes=10,
                        ),
                    ),
                    "producing_method": "thumbnail@1",
                    "parameters_sha256": "d" * 64,
                }
            )
        # A and C may share a physical input. Apply the new metadata to both references.
        inputs = [x.model_copy(update={"asset": asset}) for x in inputs]
    with pytest.raises(WorkflowValidationError) as caught:
        compile_fixture(
            d.model_copy(update={"nodes": tuple(nodes), "edges": edges, "inputs": tuple(inputs)})
        )
    assert expected in {x.code for x in caught.value.issues}


def test_frozen_plan_tampering_is_not_admitted_by_a_new_digest() -> None:
    plan = compile_fixture(graph())
    last = plan.nodes[-1]
    changed = last.model_copy(
        update={"inputs": (last.inputs[0].model_copy(update={"source_key": "f" * 64}),)}
    )
    altered = plan.model_copy(update={"nodes": (*plan.nodes[:-1], changed)})
    assert execution_plan_digest(altered) != execution_plan_digest(plan)
    with pytest.raises(ValueError, match="trusted recompilation"):
        verify_execution_plan(altered, (registration(),))


@pytest.mark.parametrize(
    "raw",
    [
        '{"schema_version":1,"schema_version":2}',
        '{"x":NaN}',
        '{"module_import":"os"}',
        '{"x":' + "[" * 34 + "0" + "]" * 34 + "}",
    ],
)
def test_untrusted_json_is_bounded_and_never_loads_code(raw: str) -> None:
    with pytest.raises(ValueError):
        load_workflow_definition(raw)


def test_new_schema_and_strict_integer_validation() -> None:
    d = graph().model_dump(mode="json")
    for field, value in (("schema_version", 2), ("revision", True), ("revision", "1")):
        invalid = {**d, field: value}
        with pytest.raises(ValidationError):
            load_workflow_definition(json.dumps(invalid))
    with pytest.raises(ValueError, match="byte budget"):
        load_workflow_definition('{"x":"' + "x" * 1048576 + '"}')
    a = source()
    assert a.description.image is not None
    broken = a.description.image.model_copy(
        update={"acquisition_range": (0.0, float("nan")), "acquisition_range_source": "unknown"}
    )
    badasset = a.model_copy(
        update={"description": a.description.model_copy(update={"image": broken})}
    )
    bad = graph().model_copy(
        update={
            "inputs": (
                WorkflowInput(node_id="A", port="source", asset=badasset),
                *graph().inputs[1:],
            )
        }
    )
    with pytest.raises(ValidationError):
        compile_fixture(bad)


def test_unknown_calibration_and_storage_depth_do_not_become_acquisition_facts() -> None:
    a = source()
    assert a.description.image is not None
    assert a.description.image.acquisition_bit_depth is None
    assert a.description.image.acquisition_range is None
    assert a.description.image.frame.physical_pixel_size_yx is None
    invalid = a.description.image.frame.model_copy(update={"origin_asset_sha256": "c" * 64})
    with pytest.raises(ValidationError, match="exact source bytes"):
        ScientificAsset.model_validate(
            a.model_copy(
                update={
                    "description": a.description.model_copy(
                        update={"image": a.description.image.model_copy(update={"frame": invalid})}
                    )
                }
            ).model_dump(mode="python")
        )


def test_measurement_columns_and_series_preserve_missing_vs_zero() -> None:
    table = TableMetadata(
        row_entity="measurement",
        columns=(
            TableColumn(
                name="value",
                dtype="float64",
                unit="detector_count",
                nullable=True,
                state_column="status",
            ),
            TableColumn(name="status", dtype="string", unit=None, nullable=False),
        ),
    )
    assert table.columns[0].nullable
    with pytest.raises(ValidationError):
        TableMetadata.model_validate(
            table.model_copy(
                update={
                    "columns": (
                        table.columns[0].model_copy(update={"nullable": False}),
                        table.columns[1],
                    )
                }
            ).model_dump(mode="python")
        )
    image = source().description.image
    assert image is not None
    missing = SeriesMetadata(
        series_id="profile",
        x_unit="pixel",
        y_unit="detector_count",
        coordinate_frame=image.frame,
        points=0,
        state="missing",
        reason="Not detected",
    )
    assert missing.points == 0 and missing.state == "missing"
    with pytest.raises(ValidationError):
        SeriesMetadata.model_validate(
            missing.model_copy(update={"state": "valid"}).model_dump(mode="python")
        )


def test_real_p002_module_plan_reopens_and_refuses_unknown_parameters(tmp_path: Path) -> None:
    folder = tmp_path / "new"
    report = freeze_wb_plan(folder)
    assert (
        report["definition_roundtrip_equal"] is True
        and report["scientific_admission"] == "not_granted"
    )
    definition = load_workflow_definition((folder / "workflow.json").read_text(encoding="utf-8"))
    entry = wb_plan_registration(definition.inputs[0].asset)
    plan = compile_workflow(definition, (entry,), ENV)
    assert plan.nodes[0].interface.module.module_id == "wb-legacy-analysis"
    node = definition.nodes[0].model_copy(update={"parameters_json": "{}"})
    with pytest.raises(WorkflowValidationError) as caught:
        compile_workflow(definition.model_copy(update={"nodes": (node,)}), (entry,), ENV)
    assert caught.value.issues[0].code == "parameters"
    with pytest.raises(FileExistsError):
        freeze_wb_plan(folder)


def test_existing_v1_schema_shapes_remain_exact() -> None:
    import tool_contracts.api as api

    frozen = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "work/evidence/P-007/v1-compatibility-baseline.json"
        ).read_text(encoding="utf-8")
    )
    for name, expected in frozen["model_schema_sha256"].items():
        model = getattr(api, name)
        raw = json.dumps(
            model.model_json_schema(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        assert hashlib.sha256(raw.encode()).hexdigest() == expected, name


def test_environment_and_scientific_metadata_participate_in_node_keys() -> None:
    definition = graph()
    original = compile_fixture(definition)
    environment_changed = compile_workflow(
        definition, (registration(),), (RuntimeVersion(name="fixture", version="2"),)
    )
    assert all(
        a.computation_key != b.computation_key
        for a, b in zip(original.nodes, environment_changed.nodes, strict=True)
    )
    asset = source()
    assert asset.description.image is not None
    image = asset.description.image
    calibrated = image.frame.model_copy(
        update={"physical_pixel_size_yx": (0.5, 0.5), "physical_unit": "um"}
    )
    new_asset = asset.model_copy(
        update={
            "description": asset.description.model_copy(
                update={"image": image.model_copy(update={"frame": calibrated})}
            )
        }
    )
    changed = compile_fixture(
        definition.model_copy(
            update={
                "inputs": tuple(
                    item.model_copy(update={"asset": new_asset}) for item in definition.inputs
                )
            }
        )
    )
    assert all(
        a.computation_key != b.computation_key
        for a, b in zip(original.nodes, changed.nodes, strict=True)
    )


def test_quantitative_ports_cannot_leave_units_or_table_columns_unspecified() -> None:
    with pytest.raises(ValidationError, match="expected unit"):
        ScientificPort(name="image", kind="raw_image", quantitative=True)
    with pytest.raises(ValidationError, match="admitted dtypes"):
        ScientificPort(name="image", kind="raw_image", quantitative=True, unit="detector_count")
    with pytest.raises(ValidationError, match="columns and units"):
        ScientificPort(name="table", kind="typed_table", quantitative=True, unit="signal")


def test_real_legacy_profile_has_a_file_backed_series_contract(tmp_path: Path) -> None:
    from wb_tool.api import execute_wb_module, load_tiff, prepare_wb_execution, wb_validation_input

    folder = tmp_path / "profile-contract"
    freeze_wb_plan(folder)
    definition = load_workflow_definition((folder / "workflow.json").read_text(encoding="utf-8"))
    original = definition.inputs[0].asset
    image = load_tiff(folder / "source.tif")
    request = prepare_wb_execution(
        original.payload, wb_validation_input("triangle_u16").request, "profile-contract"
    )
    result = execute_wb_module(image, request)
    assert result.lanes[0].bands[0].signal == 4000.0
    profile = result.lanes[0].profiles
    assert profile is not None and profile.raw == (1000.0, 2000.0, 3000.0, 2000.0, 1000.0)
    curve = folder / "raw-profile.json"
    curve.write_text(
        json.dumps({"x": list(range(5)), "y": profile.raw, "state": "valid"}), encoding="utf-8"
    )
    assert original.description.image is not None
    series = SeriesMetadata(
        series_id="lane_profile",
        x_unit="pixel",
        y_unit="detector_count",
        coordinate_frame=original.description.image.frame,
        points=5,
        state="valid",
        reason=None,
    )
    asset = ScientificAsset(
        payload=AssetRef(
            asset_id="profile",
            relative_path="raw-profile.json",
            sha256=hashlib.sha256(curve.read_bytes()).hexdigest(),
            size_bytes=curve.stat().st_size,
        ),
        sample_id=original.sample_id,
        description=ScientificType(kind="series", unit="detector_count", series=series),
        parent_payloads=(original.payload,),
        producing_method="profile_integral@1",
        parameters_sha256=request.parameters_sha256,
    )
    assert ScientificAsset.model_validate_json(asset.model_dump_json()) == asset
    with pytest.raises(ValidationError, match="quantitative y unit"):
        ScientificType(kind="series", unit="concentration", series=series)
