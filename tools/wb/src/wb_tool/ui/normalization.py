"""Explicit source/sample pairing and bounded derived-result presentation, with no I/O."""

from typing import cast

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from wb_tool.application.figure_project import WBFigureProject
from wb_tool.application.project_normalization import (
    ControlMode,
    NormalizationPlan,
    NormalizationSnapshot,
    SamplePair,
    WBNormalizedProject,
)

STATUS_NAMES = {
    "valid": "有效",
    "pending_review": "待确认",
    "excluded": "已排除",
    "unmatched": "未配对",
    "invalid_target": "目标不可用",
    "invalid_reference": "参照不可用",
    "invalid_ratio": "比值无效",
    "stale": "关联已过期",
    "control_unavailable": "对照不可用",
    "not_requested": "未启用",
    "unconfigured": "未配置",
    "unconfirmed": "OCR待确认",
    "unbound": "OCR未关联",
    "ocr_unavailable": "OCR证据不可用",
}


class NormalizationResults(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._snapshot = NormalizationSnapshot()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        controls = QHBoxLayout()
        self.labels = QComboBox()
        self.labels.addItems(["项目原图行", "已配置的OCR关联行"])
        self.page = QSpinBox()
        self.page.setRange(1, 1)
        self.count = QLabel("尚无归一化结果")
        controls.addWidget(self.labels)
        controls.addWidget(QLabel("页（每页200项）"))
        controls.addWidget(self.page)
        controls.addWidget(self.count)
        layout.addLayout(controls)
        self.table = QTableWidget(0, 13)
        self.table.setHorizontalHeaderLabels(
            [
                "Fig",
                "蛋白",
                "样本",
                "目标泳道",
                "参照泳道",
                "对照",
                "目标积分",
                "参照积分",
                "目标/参照",
                "对照均值",
                "相对值",
                "状态",
                "原因",
            ]
        )
        layout.addWidget(self.table)
        self.labels.currentIndexChanged.connect(self._page)
        self.page.valueChanged.connect(self._page)

    def invalidate(self) -> None:
        self._snapshot = NormalizationSnapshot()
        self.table.setRowCount(0)
        self.count.setText("内容改变，等待刷新")

    def show_snapshot(self, snapshot: NormalizationSnapshot) -> None:
        self._snapshot = snapshot
        self._page()

    def _page(self, *_args: object) -> None:
        all_cells = self._snapshot.ocr_cells if self.labels.currentIndex() else self._snapshot.cells
        self.page.setMaximum(max(1, (len(all_cells) + 199) // 200))
        start = (self.page.value() - 1) * 200
        cells = all_cells[start : start + 200]
        self.table.setRowCount(len(cells))
        self.count.setText(f"共 {len(all_cells)} 项")
        for i, c in enumerate(cells):
            numbers = (
                c.target.value if c.target else None,
                c.reference.value if c.reference else None,
                c.ratio,
                c.control_mean,
                c.relative,
            )
            texts = (
                c.figure,
                c.protein,
                c.sample,
                str(c.target_lane),
                str(c.reference_lane) if c.reference_lane else "",
                "是" if c.control else "否",
                *("" if v is None else format(v, ".12g") for v in numbers),
                STATUS_NAMES.get(c.ratio_status, c.ratio_status)
                + " / "
                + STATUS_NAMES.get(c.relative_status, c.relative_status),
                c.ratio_reason or c.relative_reason,
            )
            for j, text in enumerate(texts):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setToolTip(
                    f"{text}\n目标行：{c.target_row_id}\n参照行：{c.reference_row_id}\n"
                    f"目标运行：{c.target.run_id if c.target else ''}\n"
                    f"参照运行：{c.reference.run_id if c.reference else ''}"
                )
                self.table.setItem(i, j, item)


class NormalizationPanel(QWidget):
    changed = Signal()
    configure_requested = Signal(str, str, str)
    remove_requested = Signal(str)
    refresh_requested = Signal()
    export_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._plans: tuple[NormalizationPlan, ...] = ()
        self._active: NormalizationPlan | None = None
        self._loading = False
        layout = QVBoxLayout(self)
        self.note = QLabel("选择已审核的目标和参照行，重建关系后逐泳道填写同一样本的对应关系。")
        self.note.setWordWrap(True)
        layout.addWidget(self.note)
        setup = QHBoxLayout()
        self.target = QComboBox()
        self.reference = QComboBox()
        self.kind = QComboBox()
        for title, value in (
            ("选择参照类型", ""),
            ("目标蛋白 / 内参", "housekeeping"),
            ("磷酸化 / 总蛋白", "phospho_total"),
        ):
            self.kind.addItem(title, value)
        for label, widget in (("目标", self.target), ("参照", self.reference)):
            setup.addWidget(QLabel(label))
            setup.addWidget(widget, 1)
        setup.addWidget(self.kind)
        create = QPushButton("创建 / 重建关系")
        create.clicked.connect(self.configure)
        setup.addWidget(create)
        layout.addLayout(setup)
        settings = QHBoxLayout()
        self.selector = QComboBox()
        settings.addWidget(QLabel("编辑关系"))
        settings.addWidget(self.selector, 1)
        self.mode = QComboBox()
        for title, value in (
            ("仅计算蛋白比值", "ratio_only"),
            ("相对单个对照", "single_control"),
            ("相对所选对照的算术均值", "control_mean"),
        ):
            self.mode.addItem(title, value)
        settings.addWidget(self.mode)
        self.confirmed = QCheckBox("已确认样本对应与参照")
        settings.addWidget(self.confirmed)
        remove = QPushButton("删除此关系")
        remove.clicked.connect(
            lambda: self.remove_requested.emit(self._active.target.row_id) if self._active else None
        )
        settings.addWidget(remove)
        layout.addLayout(settings)
        self.pairs = QTableWidget(0, 5)
        self.pairs.setHorizontalHeaderLabels(
            ["目标泳道", "样本 / 重复编号", "对应参照泳道（留空未配）", "包含", "对照"]
        )
        self.pairs.setColumnWidth(1, 190)
        self.pairs.setColumnWidth(2, 210)
        layout.addWidget(self.pairs)
        notes = QHBoxLayout()
        notes.addWidget(QLabel("实验对应说明"))
        self.notes = QLineEdit()
        notes.addWidget(self.notes)
        layout.addLayout(notes)
        layout.addWidget(
            QLabel("仅对已核验的原图积分计算；选择对照后再确认。改变对应关系会撤回确认。")
        )
        actions = QHBoxLayout()
        for title, callback in (
            ("刷新归一化结果", self.refresh_requested.emit),
            ("导出当前标签视图 XLSX / CSV", self.export_requested.emit),
        ):
            button = QPushButton(title)
            button.clicked.connect(callback)
            actions.addWidget(button)
        layout.addLayout(actions)
        self.result_view = NormalizationResults()
        self.results = self.result_view.table
        layout.addWidget(self.result_view, 1)
        self.selector.activated.connect(self._switch)
        self.pairs.cellChanged.connect(self._edited)
        self.kind.currentIndexChanged.connect(self._edited)
        self.mode.currentIndexChanged.connect(self._edited)
        self.notes.textEdited.connect(self._edited)
        self.confirmed.toggled.connect(lambda: self._edited(confirmation=True))

    def configure(self) -> None:
        target, reference, kind = (
            w.currentData() for w in (self.target, self.reference, self.kind)
        )
        if not all(isinstance(v, str) and v for v in (target, reference, kind)):
            self.note.setText("请选择目标行、参照行和参照类型。")
            return
        self.configure_requested.emit(target, reference, kind)

    def plans(self) -> tuple[NormalizationPlan, ...]:
        if self._active is None:
            return self._plans
        pairs: list[SamplePair] = []
        for i, original in enumerate(self._active.pairs):
            sample, reference, included, control = (self.pairs.item(i, c) for c in range(1, 5))
            if any(item is None for item in (sample, reference, included, control)):
                raise ValueError("样本对应表不完整")
            assert (
                sample is not None
                and reference is not None
                and included is not None
                and control is not None
            )
            raw = reference.text().strip()
            pairs.append(
                SamplePair(
                    target_lane=original.target_lane,
                    sample=sample.text().strip(),
                    reference_lane=int(raw) if raw else None,
                    included=included.checkState() == Qt.CheckState.Checked,
                    control=control.checkState() == Qt.CheckState.Checked,
                )
            )
        kind, mode = self.kind.currentData(), self.mode.currentData()
        if kind not in ("housekeeping", "phospho_total"):
            raise ValueError("请选择参照类型")
        plan = NormalizationPlan(
            target=self._active.target,
            reference=self._active.reference,
            kind=kind,
            control_mode=cast(ControlMode, mode),
            pairs=tuple(pairs),
            confirmed=self.confirmed.isChecked(),
            notes=self.notes.text(),
        )
        return tuple(plan if p.target.row_id == plan.target.row_id else p for p in self._plans)

    def restore(self, project: WBFigureProject) -> None:
        selected = self._active.target.row_id if self._active else ""
        self._loading = True
        self._active = None
        self._plans = project.normalizations if isinstance(project, WBNormalizedProject) else ()
        self.selector.clear()
        self.selector.addItem("选择已有关系", "")
        rows = {r.row_id: r for r in project.rows}
        for plan in self._plans:
            row = rows.get(plan.target.row_id)
            self.selector.addItem(
                f"{row.figure} · {row.protein} · {row.filename}" if row else "已删除的目标行",
                plan.target.row_id,
            )
        self.refresh_targets(project)
        index = self.selector.findData(selected)
        self.selector.setCurrentIndex(index if index > 0 else (1 if self._plans else 0))
        self._loading = False
        self._load(self.selector.currentData())
        self.result_view.invalidate()

    def refresh_targets(self, project: WBFigureProject) -> None:
        for widget in (self.target, self.reference):
            selected = widget.currentData()
            widget.clear()
            widget.addItem("选择已审核行", "")
            for row in project.rows:
                if row.source and row.roi and row.reviewed:
                    widget.addItem(f"{row.figure} · {row.protein} · {row.filename}", row.row_id)
            widget.setCurrentIndex(max(0, widget.findData(selected)))

    def _switch(self, _index: int) -> None:
        if self._loading:
            return
        try:
            self._plans = self.plans()
        except ValueError as error:
            self.note.setText(str(error))
            self.selector.setCurrentIndex(
                self.selector.findData(self._active.target.row_id) if self._active else 0
            )
            return
        self._load(self.selector.currentData())

    def _load(self, row_id: object) -> None:
        self._loading = True
        plan = next((p for p in self._plans if p.target.row_id == row_id), None)
        self._active = plan
        self.pairs.setRowCount(len(plan.pairs) if plan else 0)
        self.confirmed.setChecked(bool(plan and plan.confirmed))
        self.notes.setText(plan.notes if plan else "")
        if plan:
            self.target.setCurrentIndex(max(0, self.target.findData(plan.target.row_id)))
            self.reference.setCurrentIndex(max(0, self.reference.findData(plan.reference.row_id)))
            self.kind.setCurrentIndex(self.kind.findData(plan.kind))
            self.mode.setCurrentIndex(self.mode.findData(plan.control_mode))
            for i, pair in enumerate(plan.pairs):
                for j, value in enumerate(
                    (
                        str(pair.target_lane),
                        pair.sample,
                        str(pair.reference_lane) if pair.reference_lane else "",
                        "",
                        "",
                    )
                ):
                    item = QTableWidgetItem(value)
                    if j == 0 or j >= 3:
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    if j >= 3:
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        checked = pair.included if j == 3 else pair.control
                        item.setCheckState(
                            Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
                        )
                    self.pairs.setItem(i, j, item)
        self._loading = False

    def _edited(self, *_args: object, confirmation: bool = False) -> None:
        if self._loading or self._active is None:
            return
        if not confirmation:
            self._loading = True
            self.confirmed.setChecked(False)
            self._loading = False
        self.result_view.invalidate()
        self.changed.emit()
