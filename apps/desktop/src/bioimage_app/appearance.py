"""Versioned UI preferences, independent of scientific project persistence."""

import json
from typing import cast

from PySide6.QtCore import QSettings

KEY = "workbench_appearance_v1"
DEFAULTS = {"theme": "forest", "density": "comfortable", "motion": "expressive"}
CHOICES = {
    "theme": {"forest", "ember", "iris", "neutral"},
    "density": {"comfortable", "compact"},
    "motion": {"expressive", "gentle", "reduced"},
}


class WorkbenchAppearance:
    def __init__(self, settings: QSettings) -> None:
        self.settings = settings
        self.values = DEFAULTS.copy()
        self.error = ""
        self.receipt = ""
        self.configured = False
        self._stored: object = None
        self.refresh()

    @staticmethod
    def validate(value: object) -> dict[str, str]:
        if not isinstance(value, dict):
            raise ValueError("外观配置字段不完整")
        fields = cast(dict[str, object], value)
        if set(fields) != set(DEFAULTS):
            raise ValueError("外观配置字段不完整")
        if any(not isinstance(v, str) or v not in CHOICES[k] for k, v in fields.items()):
            raise ValueError("外观配置包含不支持的选项")
        return cast(dict[str, str], fields).copy()

    def refresh(self) -> None:
        """Called at a bounded interval; QSettings.sync imports other windows' writes."""
        self.settings.sync()
        raw = self.settings.value(KEY, "")
        if raw == self._stored:
            return
        self._stored = raw
        if not raw:
            self.values, self.configured = DEFAULTS.copy(), False
            return
        try:
            if not isinstance(raw, str) or len(raw) > 2048:
                raise ValueError("已保存外观配置超出预算")
            data: object = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("已保存外观配置版本不支持")
            fields = cast(dict[str, object], data)
            if type(fields.get("schema_version")) is not int or fields.get("schema_version") != 1:
                raise ValueError("已保存外观配置版本不支持")
            self.values = self.validate(fields.get("values"))
            self.configured, self.error = True, ""
        except (ValueError, TypeError) as error:
            self.error = f"{error}；当前使用上次有效外观，原设置保留。"

    def update(self, values: object, receipt: str, version: object) -> None:
        self.receipt = receipt
        try:
            if type(version) is not int or version != 1:
                raise ValueError("外观配置版本不支持")
            selected = self.validate(values)
            previous = self.settings.value(KEY, "")
            encoded = json.dumps({"schema_version": 1, "values": selected}, sort_keys=True)
            self.settings.setValue(KEY, encoded)
            self.settings.sync()
            if self.settings.status() != QSettings.Status.NoError:
                self.settings.setValue(KEY, previous)
                self.settings.sync()
                raise OSError("外观保存失败，已恢复上次配置。请检查设置目录后重试。")
            self.values, self._stored = selected, encoded
            self.configured, self.error = True, ""
        except (ValueError, OSError) as error:
            self.error = str(error)

    def snapshot(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "values": self.values.copy(),
            "configured": self.configured,
            "receipt": self.receipt,
            "error": self.error,
        }
