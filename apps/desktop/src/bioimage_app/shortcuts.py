"""Fixed, versioned workbench action catalog and bounded local preference storage."""

import json
import re
from pathlib import Path
from typing import cast

from PySide6.QtCore import QSettings

_KEY = "workbench_shortcuts_v1"
_PATTERN = re.compile(
    r"^(?:Ctrl\+)?(?:Alt\+)?(?:Shift\+)?(?:[A-Z0-9]|F[1-9]|F1[0-2]|ArrowUp|ArrowDown|ArrowLeft|ArrowRight|Space|Enter)$"
)


class WorkbenchShortcuts:
    def __init__(self, settings: QSettings) -> None:
        self.settings = settings
        raw: object = json.loads(
            Path(__file__)
            .with_name("web_ui")
            .joinpath("shortcut_actions.json")
            .read_text(encoding="utf-8")
        )
        if not isinstance(raw, dict):
            raise ValueError("快捷键目录格式无效")
        self.catalog = cast(dict[str, object], raw)
        entries = self.catalog.get("actions")
        if not isinstance(entries, list):
            raise ValueError("快捷键目录缺少动作")
        self.defaults: dict[str, str] = {}
        for item in cast(list[object], entries):
            if not isinstance(item, dict):
                raise ValueError("快捷键动作格式无效")
            entry = cast(dict[str, object], item)
            action, binding = entry.get("id"), entry.get("default")
            if (
                not isinstance(action, str)
                or not isinstance(binding, str)
                or action in self.defaults
            ):
                raise ValueError("快捷键动作身份无效")
            self.defaults[action] = binding
        reserved = self.catalog.get("reserved")
        if not isinstance(reserved, list) or any(
            not isinstance(v, str) for v in cast(list[object], reserved)
        ):
            raise ValueError("保留快捷键格式无效")
        self.reserved = set(cast(list[str], reserved))
        self.bindings = self.validate({})
        self.error = ""
        self.receipt = ""
        stored = settings.value(_KEY, "")
        if stored:
            try:
                if not isinstance(stored, str) or len(stored) > 32768:
                    raise ValueError("已保存快捷键超出预算")
                value: object = json.loads(stored)
                if not isinstance(value, dict):
                    raise ValueError("已保存快捷键格式无效")
                fields = cast(dict[str, object], value)
                if fields.get("schema_version") != 1:
                    raise ValueError("已保存快捷键版本不支持")
                self.bindings = self.validate(fields.get("bindings"))
            except (ValueError, TypeError) as error:
                self.error = f"{error}；当前使用默认快捷键，原设置保留。"

    def validate(self, overrides: object) -> dict[str, str]:
        if not isinstance(overrides, dict):
            raise ValueError("快捷键必须是动作与组合键的映射")
        entries = cast(dict[object, object], overrides)
        if any(not isinstance(key, str) or key not in self.defaults for key in entries):
            raise ValueError("快捷键包含未知动作")
        bindings = self.defaults.copy()
        for key, value in entries.items():
            if not isinstance(value, str) or len(value) > 64:
                raise ValueError("快捷键组合格式无效")
            if value and (not _PATTERN.fullmatch(value) or "+" not in value):
                raise ValueError("请使用 Ctrl、Alt 或 Shift 加字母、数字或功能键")
            if value in self.reserved or (value == "Ctrl+Z" and key != "edit.undo"):
                raise ValueError("此组合键保留给系统或文本编辑")
            bindings[cast(str, key)] = value
        used: dict[str, str] = {}
        for key, value in bindings.items():
            if value and value in used:
                raise ValueError(f"组合键 {value} 同时绑定 {used[value]} 与 {key}")
            if value:
                used[value] = key
        return bindings

    def update(self, overrides: object, receipt: str) -> None:
        self.receipt = receipt
        try:
            bindings = self.validate(overrides)
            encoded = json.dumps({"schema_version": 1, "bindings": bindings}, sort_keys=True)
            previous = self.settings.value(_KEY, "")
            self.settings.setValue(_KEY, encoded)
            self.settings.sync()
            if self.settings.status() != QSettings.Status.NoError:
                self.settings.setValue(_KEY, previous)
                raise OSError("快捷键保存失败，当前绑定保持；请检查设置目录")
            self.bindings, self.error = bindings, ""
        except (ValueError, OSError) as error:
            self.error = str(error)

    def snapshot(self) -> dict[str, object]:
        return {
            **self.catalog,
            "bindings": self.bindings,
            "error": self.error,
            "receipt": self.receipt,
        }
