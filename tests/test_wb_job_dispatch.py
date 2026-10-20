"""Future tasks cannot fall through to document encoding and report success."""

import ast
import inspect
from pathlib import Path
from typing import Literal, cast, get_args, get_type_hints

from pytestqt.qtbot import QtBot
from wb_tool.api import WBFigureProject, WBJob, WBReply, create_wb_background


def test_unknown_operation_fails_without_encoding_and_queue_remains_usable(qtbot: QtBot) -> None:
    background = create_wb_background()
    project = WBFigureProject(project_id="dispatch-test")
    replies: list[WBReply] = []

    def received(value: object) -> None:
        assert isinstance(value, WBReply)
        replies.append(value)

    background.replied.connect(received)
    try:
        # Deliberately emulate an untyped caller or a future enum member whose
        # runtime branch has not been implemented. Dataclasses do not validate it.
        operation = cast(Literal["encode"], "future_unimplemented_operation")
        background.submit(WBJob(operation, document=project))
        qtbot.waitUntil(lambda: len(replies) == 1, timeout=5000)
        reply = replies[0]
        assert reply.value is None and "未知WB后台操作" in reply.error
        background.submit(WBJob("encode", document=project))
        qtbot.waitUntil(lambda: len(replies) == 2, timeout=5000)
        reply = replies[1]
        assert not reply.error and reply.value == project.model_dump_json().encode("utf-8")
    finally:
        with qtbot.waitSignal(background.closed, timeout=5000):
            background.shutdown()


def test_every_declared_operation_has_an_explicit_dispatch_condition() -> None:
    # Supplement the runtime rejection test with a maintenance tripwire. This
    # proves branch presence, not scientific correctness of every operation.
    path = inspect.getsourcefile(create_wb_background)
    assert path is not None
    source = Path(path).with_name("ui") / "background.py"
    handled: set[str] = set()
    for node in ast.walk(ast.parse(source.read_text(encoding="utf-8"))):
        if not isinstance(node, ast.Compare) or not isinstance(node.left, ast.Attribute):
            continue
        if node.left.attr != "operation" or not isinstance(node.left.value, ast.Name):
            continue
        if node.left.value.id != "job":
            continue
        for comparator in node.comparators:
            for value in ast.walk(comparator):
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    handled.add(value.value)
    assert handled == set(get_args(get_type_hints(WBJob)["operation"]))
