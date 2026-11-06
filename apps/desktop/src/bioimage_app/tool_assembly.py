"""Known tool availability, frozen per window; settings apply on the next start."""

import json
from importlib.util import find_spec

from PySide6.QtCore import QObject, QSettings, Signal, Slot

TOOLS = {"wb": ("wb_tool", "WB"), "nuclei": ("nuclei_tool", "核分割"), "bca": ("bca_tool", "BCA")}


class ToolAssembly(QObject):
    changed = Signal(str)
    failed = Signal(str)

    def __init__(self, settings: QSettings, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.states = {
            key: "missing"
            if find_spec(package) is None
            else "enabled"
            if settings.value(f"tools/{key}/enabled", True, type=bool)
            else "disabled"
            for key, (package, _title) in TOOLS.items()
        }

    def available(self, tool: str) -> bool:
        return self.states[tool] == "enabled"

    def require(self, tool: str) -> None:
        if not self.available(tool):
            raise ValueError(self.reason(tool) + "；项目和原图保持原样，请准备工具后重启。")

    def reason(self, tool: str) -> str:
        return (
            TOOLS[tool][1]
            + {"missing": "未安装", "disabled": "已停用", "enabled": "已启用"}[self.states[tool]]
        )

    @Slot()
    def refresh(self) -> None:
        self.changed.emit(
            json.dumps(
                {
                    key: {
                        "state": self.states[key],
                        "message": self.reason(key),
                        "nextEnabled": self.settings.value(f"tools/{key}/enabled", True, type=bool),
                    }
                    for key in TOOLS
                },
                ensure_ascii=False,
            )
        )

    @Slot(str, bool)
    def setEnabled(self, tool: str, enabled: bool) -> None:
        if tool not in TOOLS:
            return
        self.settings.setValue(f"tools/{tool}/enabled", enabled)
        self.settings.sync()
        if self.settings.status() != QSettings.Status.NoError:
            self.failed.emit("工具设置写入失败，请检查设置目录权限；本次会话保持原装配。")
            return
        self.refresh()


class PlatformBridge(QObject):
    """Platform session channel when the optional WB editor is not assembled."""

    stateChanged = Signal(str)
    sessionRequested = Signal(str, str)
    sessionStateChanged = Signal(str)
    session_epoch = 0

    def __init__(self, assembly: ToolAssembly, parent: QObject) -> None:
        super().__init__(parent)
        self.assembly = assembly

    @Slot(str, str)
    def session(self, action: str, payload: str = "{}") -> None:
        if len(payload) <= 8192:
            self.sessionRequested.emit(action, payload)

    @Slot(str, str)
    def request(self, action: str, payload: str = "{}") -> None:
        self.sessionRequested.emit("refresh" if action == "refresh" else "missing_wb", "{}")
