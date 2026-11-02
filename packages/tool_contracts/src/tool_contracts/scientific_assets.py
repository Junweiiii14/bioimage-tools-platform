"""Small semantic descriptions compose AssetRef v1; payloads remain external files."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from tool_contracts.contracts_v1 import (
    AssetRef,
    Digest,
    FrozenContract,
    Identifier,
    ShortText,
    VersionOne,
)

ScientificKind = Literal[
    "raw_image",
    "analysis_image",
    "display_image",
    "typed_table",
    "series",
    "run_manifest",
    "analysis_result",
]
ImageDtype = Literal["uint8", "uint16", "float64"]


class CoordinateFrame(FrozenContract):
    frame_id: Identifier
    origin_asset_sha256: Digest
    convention: Literal["integer_pixel_centres_yx@1"] = "integer_pixel_centres_yx@1"
    spatial_unit: Literal["pixel"] = "pixel"
    physical_pixel_size_yx: (
        tuple[Annotated[float, Field(gt=0)], Annotated[float, Field(gt=0)]] | None
    )
    physical_unit: ShortText | None

    @model_validator(mode="after")
    def calibration_pair(self) -> Self:
        if (self.physical_pixel_size_yx is None) != (self.physical_unit is None):
            raise ValueError("Unknown physical calibration must remain explicit")
        return self


class ImageMetadata(FrozenContract):
    dtype: ImageDtype
    axes: tuple[Literal["y"], Literal["x"]]
    shape: tuple[Annotated[int, Field(gt=0, le=100000)], Annotated[int, Field(gt=0, le=100000)]]
    acquisition_bit_depth: Annotated[int, Field(ge=1, le=64)] | None
    acquisition_range: tuple[float, float] | None
    acquisition_range_source: ShortText | None
    frame: CoordinateFrame
    valid_mask: AssetRef | None = None

    @model_validator(mode="after")
    def intensity_provenance(self) -> Self:
        if (self.acquisition_range is None) != (self.acquisition_range_source is None):
            raise ValueError("Acquisition range requires its independent source")
        if (
            self.acquisition_range is not None
            and self.acquisition_range[0] >= self.acquisition_range[1]
        ):
            raise ValueError("Acquisition range must increase")
        return self


class TableColumn(FrozenContract):
    name: Identifier
    dtype: Literal["string", "int64", "float64", "bool"]
    unit: ShortText | None
    nullable: bool
    state_column: Identifier | None = None


class TableMetadata(FrozenContract):
    row_entity: ShortText
    columns: Annotated[tuple[TableColumn, ...], Field(min_length=1, max_length=64)]
    state_vocabulary: ShortText = "valid_missing_invalid_review@1"
    states: Annotated[tuple[ShortText, ...], Field(min_length=2, max_length=16)] = (
        "valid",
        "missing",
        "invalid",
        "review",
    )

    @model_validator(mode="after")
    def column_integrity(self) -> Self:
        if len(set(self.states)) != len(self.states) or "valid" not in self.states:
            raise ValueError("State vocabulary requires unique states including valid")
        columns = {x.name: x for x in self.columns}
        if len(columns) != len(self.columns):
            raise ValueError("Duplicate table column")
        for column in self.columns:
            if column.dtype in ("int64", "float64") and column.unit is None:
                raise ValueError("Numeric columns need an explicit unit, including dimensionless")
            if column.state_column is not None:
                state = columns.get(column.state_column)
                if state is None or state.dtype != "string" or state.nullable or state.state_column:
                    raise ValueError("A measurement state requires a non-null string column")
                if not column.nullable:
                    raise ValueError("Non-valid measurements require null, never a fabricated zero")
        return self


class SeriesMetadata(FrozenContract):
    series_id: Identifier
    x_unit: ShortText
    y_unit: ShortText
    coordinate_frame: CoordinateFrame
    points: Annotated[int, Field(ge=0, le=10000000)]
    state: Literal["valid", "missing", "invalid", "review"]
    reason: ShortText | None

    @model_validator(mode="after")
    def series_state(self) -> Self:
        if self.state != "valid" and not self.reason:
            raise ValueError("Non-valid series require a reason")
        if self.state == "valid" and self.points == 0:
            raise ValueError("An empty series cannot impersonate a valid measurement")
        return self


class ScientificType(FrozenContract):
    """A frozen semantic type, without a second physical asset identity."""

    kind: ScientificKind
    unit: ShortText | None
    image: ImageMetadata | None = None
    table: TableMetadata | None = None
    series: SeriesMetadata | None = None

    @model_validator(mode="after")
    def kind_metadata(self) -> Self:
        expected = (
            self.kind in ("raw_image", "analysis_image", "display_image"),
            self.kind == "typed_table",
            self.kind == "series",
        )
        actual = (self.image is not None, self.table is not None, self.series is not None)
        if expected != actual:
            raise ValueError("Scientific kind and metadata disagree")
        if self.series is not None and self.unit != self.series.y_unit:
            raise ValueError("Series unit must agree with its quantitative y unit")
        if self.image is not None:
            if self.kind == "raw_image" and self.image.dtype not in ("uint8", "uint16"):
                raise ValueError("M1 raw images retain the admitted integer source path")
            if self.kind == "analysis_image" and self.image.valid_mask is None:
                raise ValueError("Analysis images need an explicit validity mask")
            if self.kind == "display_image" and self.image.dtype != "uint8":
                raise ValueError("Display images use the explicit RGB8/thumbnail role")
        return self


class ScientificAsset(FrozenContract):
    schema_version: VersionOne = 1
    payload: AssetRef
    sample_id: Identifier
    description: ScientificType
    parent_payloads: Annotated[tuple[AssetRef, ...], Field(max_length=16)] = ()
    producing_method: ShortText | None
    parameters_sha256: Digest | None

    @model_validator(mode="after")
    def provenance(self) -> Self:
        if self.payload.size_bytes == 0:
            raise ValueError("Scientific payload must be a nonempty file")
        if len({p.asset_id for p in self.parent_payloads}) != len(self.parent_payloads):
            raise ValueError("Duplicate scientific parent")
        if any(p.asset_id == self.payload.asset_id for p in self.parent_payloads):
            raise ValueError("Scientific asset cannot be its own parent")
        if (self.producing_method is None) != (self.parameters_sha256 is None):
            raise ValueError("Producing method and parameters provenance must be paired")
        if self.description.kind in ("analysis_image", "display_image") and (
            not self.parent_payloads or self.producing_method is None
        ):
            raise ValueError("Derived images require source and versioned method provenance")
        if (
            self.description.kind == "raw_image"
            and self.description.image is not None
            and self.description.image.frame.origin_asset_sha256 != self.payload.sha256
        ):
            raise ValueError("Raw coordinates must identify the exact source bytes")
        return self
