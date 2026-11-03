"""Versioned portable templates shared by the editor and batch CLI."""

import json
from typing import Literal

from platform_runtime.api import load_workflow_definition
from pydantic import BaseModel, ConfigDict
from tool_contracts.api import (
    NodePosition,
    WorkflowDefinition,
    WorkflowLayout,
    canonical_module_json,
)


class WorkflowTemplate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)
    template_version: Literal[1] = 1
    definition: WorkflowDefinition
    layout: WorkflowLayout


def load_workflow_template(raw: str) -> WorkflowTemplate:
    """Accept the original definition format and the layout-preserving v1 envelope."""
    canonical = canonical_module_json(raw)
    if "template_version" in json.loads(canonical):
        return WorkflowTemplate.model_validate_json(canonical, strict=True)
    definition = load_workflow_definition(canonical)
    return WorkflowTemplate(
        definition=definition,
        layout=WorkflowLayout(
            positions=tuple(
                NodePosition(node_id=node.node_id, x=float(index * 300), y=40.0)
                for index, node in enumerate(definition.nodes)
            )
        ),
    )
