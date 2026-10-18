"""Schema9 records original-sheet OCR evidence without rewriting older projects."""

from pydantic import Field, model_validator

from wb_tool.application.automatic import WBAutomaticProject
from wb_tool.domain.worksheet import OCRRecognition


class WBPartitionProject(WBAutomaticProject):
    schema_version: int = Field(default=9, ge=9, le=9)
    partition_sources: tuple[OCRRecognition, ...] = Field(default=(), max_length=32)

    @model_validator(mode="after")
    def partition_identity(self) -> "WBPartitionProject":
        sources = {row.source.sha256 for row in self.rows if row.source}
        hashes = [e.source_sha256 for e in self.partition_sources]
        if len(set(hashes)) != len(hashes) or not set(hashes) <= sources:
            raise ValueError("Fig切分来源重复或不属于当前项目")
        return self
