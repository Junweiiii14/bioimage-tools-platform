"""Portable settings only; workspace and scientific identities never enter a template."""

from dataclasses import dataclass
from typing import Literal

from pydantic import Field, model_validator

from wb_tool.application.document import DocumentIO
from wb_tool.application.figure_project import FigureTemplate
from wb_tool.application.laboratory_layout import FigureLayoutStyle


class TemplateFont(DocumentIO):
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(gt=0, le=32 * 1024 * 1024)
    filename: Literal["font.ttf", "font.otf", "font.ttc"]


class PortableFigureTemplate(DocumentIO):
    document_type: Literal["wb_figure_template"] = "wb_figure_template"
    schema_version: int = Field(default=1, ge=1, le=1)
    template: FigureTemplate
    layout_style: FigureLayoutStyle | None = None
    font: TemplateFont | None = None

    @model_validator(mode="after")
    def portable(self) -> "PortableFigureTemplate":
        if self.template.font is not None:
            raise ValueError("独立模板不能携带旧工作区字体引用")
        return self


@dataclass(frozen=True)
class LoadedFigureTemplate:
    spec: PortableFigureTemplate
    font_data: bytes = b""
