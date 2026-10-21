"""Bounded, read-only Fig previews independent of the running batch's identity."""

import base64
import json
from typing import TYPE_CHECKING

from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QImage, QImageWriter
from wb_tool.api import FigureRender, WBIntakeFigureProject, WBJob, WBReply, intake_figure_digest

from bioimage_app.storage import StorageCommand, StorageReply

if TYPE_CHECKING:
    from bioimage_app.figure_window import FigureProjectWindow


class IntakeFigurePresentation:
    def __init__(self, host: "FigureProjectWindow") -> None:
        self.host = host
        self.serial = 0
        self._request = 0
        self._selected: tuple[str, str, str, str, str] | None = None
        self._cache: dict[tuple[str, str, str, str, str], dict[str, object]] = {}
        self._error = ""
        self._loading = False

    def _identity(
        self, project: WBIntakeFigureProject, figure_id: str
    ) -> tuple[str, str, str, str, str]:
        evidence = next((e for e in project.intake_figures if e.figure_id == figure_id), None)
        if evidence is None:
            raise ValueError("当前 Fig 尚未生成已保存的图像")
        if evidence.input_digest != intake_figure_digest(project, figure_id):
            raise ValueError("当前 Fig 图片已过期，请先重新生成")
        return (
            self.host.workspace_path,
            project.project_id,
            figure_id,
            evidence.input_digest,
            evidence.image.sha256,
        )

    def snapshot(self, project: WBIntakeFigureProject) -> dict[str, object] | None:
        key = self._selected
        if key is None:
            return None
        try:
            if self._identity(project, key[2]) != key:
                return None
        except ValueError:
            return None
        return {
            "figureId": key[2],
            "loading": self._loading,
            "error": self._error,
            **self._cache.get(key, {}),
        }

    def remember(self, project: WBIntakeFigureProject, rendered: FigureRender) -> None:
        manifest = json.loads(rendered.manifest_json)
        binding = manifest["preview_binding"]
        key = self._identity(project, binding["figure_id"])
        if key[3:] != (binding["input_digest"], binding["asset_sha256"]):
            raise ValueError("Fig 显示回复与已提交资产不一致")
        image = QImage(
            rendered.rgb,
            rendered.width,
            rendered.height,
            rendered.width * 3,
            QImage.Format.Format_RGB888,
        )
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        if not QImageWriter(buffer, b"png").write(image):
            raise ValueError("Fig 图片显示编码失败")
        url = "data:image/png;base64," + base64.b64encode(buffer.data().data()).decode("ascii")
        self._cache.pop(key, None)
        self._cache[key] = {
            "image": url,
            "width": rendered.width,
            "height": rendered.height,
            "regions": manifest["rows"],
        }
        while len(self._cache) > 4 or (
            len(self._cache) > 1
            and sum(len(str(v["image"])) for v in self._cache.values()) > 16_000_000
        ):
            self._cache.pop(next(iter(self._cache)))
        self.serial += 1

    def request(self, project: WBIntakeFigureProject, figure_id: str) -> None:
        key = self._identity(project, figure_id)
        if self._selected == key and (self._loading or key in self._cache):
            return
        self._request += 1
        request = self._request
        self._selected, self._error, self._loading = key, "", key not in self._cache
        self.serial += 1
        if not self._loading:
            return
        evidence = next(e for e in project.intake_figures if e.figure_id == figure_id)

        def current() -> bool:
            value = self.host.view.project()
            if (
                self.host.is_closing
                or request != self._request
                or not isinstance(value, WBIntakeFigureProject)
            ):
                return False
            try:
                return self._identity(value, figure_id) == key
            except ValueError:
                return False

        def fail(message: str) -> None:
            if current():
                self._loading, self._error = False, message
                self.serial += 1

        def shown(reply: WBReply) -> None:
            if not current():
                return
            if reply.error or not isinstance(reply.value, FigureRender):
                fail(reply.error or "Fig 图片读取失败；可重新加载")
                return
            try:
                self.remember(project, reply.value)
                self._loading = False
            except ValueError as error:
                fail(str(error))

        def resolved(reply: StorageReply) -> None:
            if not current():
                return
            if reply.error_code or not isinstance(reply.value, str):
                fail(reply.message or "已保存的 Fig 图片不可用")
                return
            self.host.submit_tool_job(
                WBJob(
                    "intake_figure_preview",
                    document=project,
                    row_id=figure_id,
                    path=reply.value,
                    cancellation=self.host.cancellation,
                ),
                shown,
                accept_errors=True,
            )

        self.host.submit_storage_job(
            StorageCommand("asset", asset=evidence.image), resolved, accept_errors=True
        )
