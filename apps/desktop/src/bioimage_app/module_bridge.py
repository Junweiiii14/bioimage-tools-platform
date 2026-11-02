"""Thin local WebChannel actions; the shared session owns all computation and storage."""

import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import cast
from uuid import uuid4

from PySide6.QtCore import QObject, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QWidget

from bioimage_app.module_session import ComparisonSession


class ComparisonBridge(QObject):
    stateChanged = Signal(str)
    idle = Signal()

    def __init__(self, parent: QWidget, unavailable: Callable[[], bool]) -> None:
        super().__init__(parent)
        self._window = parent
        self._unavailable = unavailable
        self._session: ComparisonSession | None = None
        self._state: dict[str, object] = {
            "state": "idle",
            "message": "选择固定样例，比较旧入口与独立模块的真实输出。",
            "workspace": "",
            "files": {},
            "tables_json": {},
        }

    @property
    def busy(self) -> bool:
        return self._session is not None

    def _emit(self) -> None:
        self.stateChanged.emit(json.dumps({**self._state, "busy": self.busy}, ensure_ascii=False))

    @Slot(str, str)
    def request(self, action: str, payload: str) -> None:
        try:
            if len(payload) > 4096:
                raise ValueError("对照操作参数过长")
            if action == "refresh":
                self._emit()
                return
            if action == "cancel":
                self.cancel()
                return
            if self.busy:
                raise ValueError("请等待当前对照结束，或先取消")
            if action == "run":
                raw: object = json.loads(payload)
                if not isinstance(raw, dict):
                    raise ValueError("无效样例参数")
                case = cast(dict[str, object], raw).get("case")
                if case not in (
                    "triangle_u8",
                    "triangle_u16",
                    "flat_zero",
                    "invalid_roi",
                    "dtype_limits",
                ):
                    raise ValueError("未知样例")
                if self._unavailable():
                    raise ValueError("当前WB任务尚未结束，请完成或取消后再运行对照")
                parent = QFileDialog.getExistingDirectory(self._window, "选择新对照工程的保存位置")
                if parent:
                    name = "WB对照-" + datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid4().hex[:6]
                    self.start_fixture_at(str(Path(parent) / name), str(case))
            elif action == "open":
                if self._unavailable():
                    raise ValueError("请等待当前WB任务结束")
                path = QFileDialog.getExistingDirectory(self._window, "打开已保存的对照工程")
                if path:
                    self.reopen_at(path)
            elif action == "reopen":
                path = self._state.get("workspace")
                if not isinstance(path, str) or not path:
                    raise ValueError("尚无可重开的对照工程")
                self.reopen_at(path)
            elif action == "folder":
                path = self._state.get("workspace")
                if not isinstance(path, str) or not path or self._state.get("state") != "succeeded":
                    raise ValueError("请先完成或重开已保存对照")
                if not QDesktopServices.openUrl(QUrl.fromLocalFile(path)):
                    raise ValueError("无法打开工程文件夹")
            else:
                raise ValueError("未知对照操作")
        except (ValueError, OSError, RuntimeError) as exc:
            self._state["message"] = str(exc)
            self._emit()

    def _new_session(self) -> ComparisonSession:
        if self.busy or self._unavailable():
            raise ValueError("当前会话忙，请等待或取消")
        session = ComparisonSession(self)
        self._session = session
        session.changed.connect(self._changed)
        session.finished.connect(self._finished)
        return session

    def start_fixture_at(self, workspace: str, case: str = "triangle_u16") -> None:
        self._new_session().start_fixture(workspace, case)

    def reopen_at(self, workspace: str) -> None:
        self._new_session().reopen(workspace)

    def cancel(self) -> None:
        if self._session is not None:
            self._session.cancel()

    @Slot(str)
    def _changed(self, payload: str) -> None:
        self._state = json.loads(payload)
        self._emit()

    @Slot(str)
    def _finished(self, payload: str) -> None:
        self._state = json.loads(payload)
        session = self._session
        self._session = None
        if session is not None:
            session.deleteLater()
        self._emit()
        self.idle.emit()
