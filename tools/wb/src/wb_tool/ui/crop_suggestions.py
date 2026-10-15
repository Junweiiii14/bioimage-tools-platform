"""Review controls for candidate snapshots; no computation or file access."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from wb_tool.application.crop_suggestions import CropSuggestion
from wb_tool.application.figure_project import FigureRow
from wb_tool.domain.crop_detection import CropDetectionSettings

_FLAGS = {
    "manual_membrane": "使用手框膜范围",
    "membrane_geometry_candidate": "膜边界须核对",
    "membrane_not_found": "未找到膜，请手框搜索范围",
    "membrane_boundary_unclear": "膜边界不明，请手框搜索范围",
    "multiple_membranes": "可能有多个膜，须手框目标膜",
    "membrane_at_image_edge": "膜触及图像边缘",
    "marker_at_membrane_edge": "左 Marker 槽触边",
    "periodic_grid_candidate": "等间距网格候选",
    "uniform_grid_fallback": "未可靠拟合泳道，已回退等分，须调整",
    "left_marker_identity_unconfirmed": "左 Marker 身份未经确认",
    "membrane_edge_signal_ignored": "忽略了膜上下边缘信号，可勾选包含边缘重检",
    "multiple_candidate_rows": "多行候选，须选择目标行",
    "no_candidate_rows": "没有达到阈值的候选行",
    "candidate_limit": "候选超过 8 行，仅保留前 8 行",
    "crop_height_exceeds_membrane": "裁剪高度超过膜高",
    "band_wider_than_crop": "信号范围超过裁剪高度",
    "dtype_limits_review": "存在灰度上下限像素，需核对饱和/背景",
}


class CropSuggestionPanel(QWidget):
    run_requested = Signal(bool)
    apply_requested = Signal(int)
    candidate_changed = Signal()
    focus_requested = Signal()
    reset_view_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)
        title = QLabel("裁剪与候选")
        title.setObjectName("exportHeading")
        root.addWidget(title)
        hint = QLabel("在右侧原图框选范围，或检测候选后逐行复核。")
        hint.setWordWrap(True)
        root.addWidget(hint)
        self.advanced_settings = QWidget()
        settings = QVBoxLayout(self.advanced_settings)
        settings.setContentsMargins(0, 0, 0, 0)
        self.polarity = QComboBox()
        self.polarity.addItems(["暗带 / 亮底", "亮带 / 暗底"])
        self.marker = QCheckBox("左侧有 Marker")
        self.marker.setChecked(True)
        self.edges = QCheckBox("包含膜上下边缘")
        self.manual = QCheckBox("当前框作为膜搜索范围")
        self.threshold = QDoubleSpinBox()
        self.threshold.setRange(2, 12)
        self.threshold.setValue(4)
        self.threshold.setPrefix("SNR ≥ ")
        for widget in (self.polarity, self.marker, self.edges, self.manual, self.threshold):
            settings.addWidget(widget)
        self.advanced_settings.hide()
        actions = QGridLayout()
        self.run_one = QPushButton("检测当前行")
        self.run_all = QPushButton("检测全部原图")
        self.run_one.clicked.connect(lambda: self.run_requested.emit(False))
        self.run_all.clicked.connect(lambda: self.run_requested.emit(True))
        self.candidates = QComboBox()
        self.candidates.setMinimumWidth(180)
        self.candidates.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.candidates.setMinimumContentsLength(12)
        self.apply = QPushButton("应用所选候选")
        self.restore = QPushButton("恢复首选候选")
        self.focus = QPushButton("聚焦膜区域")
        self.reset_view = QPushButton("显示全图")
        self.focus.clicked.connect(self.focus_requested)
        self.reset_view.clicked.connect(self.reset_view_requested)
        self.apply.clicked.connect(
            lambda: self.apply_requested.emit(self.candidates.currentIndex())
        )
        self.restore.clicked.connect(lambda: self.apply_requested.emit(0))
        self.candidates.currentIndexChanged.connect(self.candidate_changed)
        actions.addWidget(self.run_one, 0, 0)
        actions.addWidget(self.run_all, 0, 1)
        actions.addWidget(self.candidates, 1, 0, 1, 2)
        actions.addWidget(self.apply, 2, 0)
        actions.addWidget(self.restore, 2, 1)
        actions.addWidget(self.focus, 3, 0)
        actions.addWidget(self.reset_view, 3, 1)
        self.apply.setObjectName("primaryAction")
        self.advanced_toggle = QCheckBox("高级检测设置")
        self.advanced_toggle.toggled.connect(self.advanced_settings.setVisible)
        actions.addWidget(self.advanced_toggle, 4, 0, 1, 2)
        root.addLayout(actions)
        root.addWidget(self.advanced_settings)
        self.details = QLabel()
        self.details.setWordWrap(True)
        root.addWidget(self.details)
        root.addStretch()
        self._shown: tuple[str, CropSuggestion | None] | None = None
        self.show_suggestion(None, None, 60)

    def settings(self, row: FigureRow, height: int) -> CropDetectionSettings:
        if self.manual.isChecked() and row.roi is None:
            raise ValueError("先在原图框出膜搜索范围，再检测当前行")
        return CropDetectionSettings(
            row.lane_count,
            height,
            "dark" if self.polarity.currentIndex() == 0 else "light",
            left_marker=self.marker.isChecked(),
            min_snr=self.threshold.value(),
            membrane_hint=row.roi if self.manual.isChecked() else None,
            include_membrane_edges=self.edges.isChecked(),
        )

    def show_suggestion(
        self, row: FigureRow | None, suggestion: CropSuggestion | None, height: int
    ) -> None:
        self.run_one.setEnabled(row is not None and row.source is not None)
        shown = (row.row_id if row else "", suggestion)
        result = suggestion.result if suggestion else None
        if shown != self._shown:
            self._shown = shown
            self.candidates.blockSignals(True)
            self.candidates.clear()
            if result and suggestion:
                for i, candidate in enumerate(result.candidates):
                    self.candidates.addItem(
                        f"{i + 1} · y={candidate.peak_y} · "
                        f"检测到 {len(candidate.detected_lanes)}/{result.settings.lane_count} 槽"
                    )
                self.candidates.setCurrentIndex(suggestion.selected_index or 0)
            self.candidates.blockSignals(False)
        stale = bool(
            row
            and suggestion
            and (
                row.lane_count != suggestion.settings.lane_count
                or height != suggestion.settings.crop_height
            )
        )
        available = bool(result and result.candidates and not stale)
        self.apply.setEnabled(available)
        self.restore.setEnabled(available)
        text = "选择原图，确认 N、裁剪高与极性后检测。橙框为建议，绿框为当前裁剪；应用后仍须审核。"
        if suggestion:
            params = suggestion.settings
            polarity = "暗带" if params.polarity == "dark" else "亮带"
            text = (
                f"已存参数：N={params.lane_count}，高={params.crop_height}，"
                f"{polarity}，阈值={params.min_snr:g}。"
            )
            if suggestion.error:
                text += "检测失败：" + suggestion.error
            elif result:
                flags = list(result.flags)
                index = self.candidates.currentIndex()
                if 0 <= index < len(result.candidates):
                    candidate = result.candidates[index]
                    flags.extend(candidate.flags)
                    text += (
                        f"弱信号槽：{candidate.weak_lanes or '无'}；"
                        f"可能空槽：{candidate.possible_empty_lanes or '无'}（不自动标空）。"
                    )
                text += "；".join(_FLAGS.get(flag, flag) for flag in flags)
            if suggestion.source_warnings:
                text += "。" + "；".join(suggestion.source_warnings)
            if stale:
                text += "。N 或裁剪高已改变，旧建议仅供查看，请重新检测。"
        self.details.setText(text)
