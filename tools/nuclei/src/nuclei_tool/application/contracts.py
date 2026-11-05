"""Small immutable research parameters; no tunable scientific defaults."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class NucleiParameters(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    schema_version: Literal[1] = 1
    method_version: Literal["stardist-fluo-p014@1"] = "stardist-fluo-p014@1"
    source_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    shape_yx: tuple[Annotated[int, Field(ge=1)], Annotated[int, Field(ge=1)]]
