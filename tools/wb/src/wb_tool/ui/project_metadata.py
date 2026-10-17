"""Editable metadata preview, explicit target selection, and opt-in field application."""

from dataclasses import replace

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
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
from wb_tool.application.project_metadata import (
    METADATA_FIELDS,
    METADATA_LABELS,
    MetadataBook,
    MetadataCell,
    MetadataEntry,
    MetadataKey,
    MetadataPreview,
    apply_metadata,
    filename_metadata,
    metadata_digest,
    preview_metadata,
)

_ALIASES = {
    "project_name": ("实验项目", "项目", "project_name"),
    "figure": ("fig", "fig编号", "figure"),
    "protein": ("蛋白", "蛋白名称", "protein"),
    "lane_count": ("n", "泳道数量", "泳道数", "lane_count"),
    "empty_lanes": ("空泳道", "空泳道情况", "empty_lanes"),
    "order": ("排列顺序", "排序", "order"),
    "notes": ("备注", "notes"),
    "key": ("原图名称", "原图", "文件名", "filename", "row_id", "sha256"),
}


class ProjectMetadataPanel(QWidget):
    import_requested = Signal()
    preview_requested = Signal(str)
    apply_requested = Signal()
    thumbnails_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.book: MetadataBook | None = None
        self.preview: MetadataPreview | None = None
        self._loading = False
        self._targets: list[QComboBox] = []
        self._target_model = QStandardItemModel(self)
        root = QVBoxLayout(self)
        self.status = QLabel("选择原图行，可批量填值或按文件名分段提取；Excel/CSV 先映射列再预览。")
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        bar = QHBoxLayout()
        for title, signal in (
            ("导入 Excel / CSV 元信息", self.import_requested),
            ("加载原图缩略图", self.thumbnails_requested),
        ):
            button = QPushButton(title)
            button.clicked.connect(signal)
            bar.addWidget(button)
        self.sheet = QComboBox()
        self.header = QSpinBox()
        self.header.setRange(1, 1025)
        bar.addWidget(self.sheet)
        bar.addWidget(QLabel("表头行"))
        bar.addWidget(self.header)
        root.addLayout(bar)
        form = QFormLayout()
        keys = QHBoxLayout()
        self.key_kind = QComboBox()
        for title, value in (
            ("完整文件名（大小写一致）", "filename"),
            ("行 ID", "row_id"),
            ("完整 SHA256", "sha256"),
        ):
            self.key_kind.addItem(title, value)
        self.columns: dict[str, QComboBox] = {key: QComboBox() for key in ("key", *METADATA_FIELDS)}
        keys.addWidget(self.key_kind)
        keys.addWidget(self.columns["key"])
        form.addRow("匹配键 / 表格列", keys)
        root.addLayout(form)
        grid = QGridLayout()
        self.enabled: dict[str, QCheckBox] = {}
        self.common: dict[str, QLineEdit] = {}
        for index, (field, label) in enumerate(zip(METADATA_FIELDS, METADATA_LABELS, strict=True)):
            check = QCheckBox(label)
            self.enabled[field] = check
            self.common[field] = QLineEdit()
            self.common[field].setPlaceholderText("共同值")
            grid.addWidget(check, 0, index)
            grid.addWidget(self.columns[field], 1, index)
            grid.addWidget(self.common[field], 2, index)
        root.addLayout(grid)
        bar = QHBoxLayout()
        self.separator = QLineEdit("_")
        self.separator.setMaximumWidth(60)
        self.pattern = QLineEdit("Fig,蛋白,N")
        bar.addWidget(QLabel("文件名分隔符"))
        bar.addWidget(self.separator)
        bar.addWidget(QLabel("各段字段（逗号分隔；忽略写 -）"))
        bar.addWidget(self.pattern, 1)
        root.addLayout(bar)
        bar = QHBoxLayout()
        for title, mode in (
            ("预览表格匹配", "table"),
            ("从所选行文件名提取", "filename"),
            ("共同值预览到所选行", "common"),
        ):
            button = QPushButton(title)
            button.clicked.connect(lambda _checked=False, m=mode: self.preview_requested.emit(m))
            bar.addWidget(button)
        apply = QPushButton("应用勾选的行与字段")
        apply.clicked.connect(self.apply_requested)
        bar.addWidget(apply)
        root.addLayout(bar)
        note = QLabel(
            "先勾选字段与预览行。空白保持原值；空泳道填“无”清空，备注填 [] 清空。"
            "顺序仅重排所选行占用的位置。实验项目是整个项目的名称。"
        )
        note.setWordWrap(True)
        root.addWidget(note)
        selection = QHBoxLayout()
        for title, checked in (("勾选所有预览行", True), ("取消勾选", False)):
            button = QPushButton(title)
            button.clicked.connect(lambda _checked=False, value=checked: self.select_entries(value))
            selection.addWidget(button)
        root.addLayout(selection)
        self.table = QTableWidget(0, 11)
        self.table.setHorizontalHeaderLabels(
            ["应用", "输入键 / 行", "目标原图行", *METADATA_LABELS, "匹配提示"]
        )
        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(1, 160)
        self.table.setColumnWidth(2, 240)
        self.table.setColumnWidth(10, 250)
        root.addWidget(self.table, 1)
        self.table.cellChanged.connect(self._corrected)
        self.sheet.currentIndexChanged.connect(self._map_columns)
        self.header.valueChanged.connect(self._map_columns)
        self.key_kind.currentIndexChanged.connect(self._settings_changed)
        for combo in self.columns.values():
            combo.currentIndexChanged.connect(self._settings_changed)
        for edit in (*self.common.values(), self.separator, self.pattern):
            edit.textChanged.connect(self._settings_changed)

    def _settings_changed(self) -> None:
        if self.preview is not None:
            self.clear_preview()
            self.status.setText("导入设置已改变，请重新生成预览。")

    def clear_preview(self) -> None:
        self.preview = None
        self._targets.clear()
        self.table.setRowCount(0)

    def install_book(self, book: MetadataBook, filename: str) -> None:
        self.book = book
        self.clear_preview()
        self.sheet.clear()
        self.sheet.addItems([sheet.name for sheet in book.sheets])
        self.header.setValue(1)
        self._map_columns()
        self.status.setText(f"已读取 {filename}；请检查表头和列映射，再生成预览。")

    def _map_columns(self) -> None:
        if self.book is None or not 0 <= self.sheet.currentIndex() < len(self.book.sheets):
            return
        self.clear_preview()
        rows = self.book.sheets[self.sheet.currentIndex()].rows
        headers = rows[self.header.value() - 1] if self.header.value() <= len(rows) else ()
        for field, combo in self.columns.items():
            combo.clear()
            combo.addItem("不导入", -1)
            for i, cell in enumerate(headers):
                combo.addItem(f"{i + 1}: {cell.text or cell.error or '空白'}", i)
            matches = [
                i
                for i, cell in enumerate(headers)
                if not cell.error and cell.text.strip().lower() in _ALIASES[field]
            ]
            if len(matches) == 1:
                combo.setCurrentIndex(matches[0] + 1)

    def build_preview(self, mode: str, project: WBFigureProject, selected: tuple[str, ...]) -> None:
        if mode == "table":
            if self.book is None or self.sheet.currentIndex() < 0:
                raise ValueError("请先导入元信息表")
            key: MetadataKey = self.key_kind.currentData()
            proposal = preview_metadata(
                project,
                self.book.sheets[self.sheet.currentIndex()],
                self.header.value() - 1,
                key,
                self.columns["key"].currentData(),
                tuple(
                    (f, c.currentData())
                    for f, c in self.columns.items()
                    if f != "key" and c.currentData() >= 0
                ),
                source=f"{self.book.sha256} / {self.sheet.currentText()}",
            )
        elif mode == "filename":
            aliases: dict[str, str] = dict(zip(METADATA_LABELS, METADATA_FIELDS, strict=True))
            fields = tuple(
                "" if item.strip() in ("", "-") else aliases.get(item.strip(), item.strip())
                for item in self.pattern.text().split(",")
            )
            proposal = filename_metadata(project, selected, self.separator.text(), fields)
        else:
            if not selected:
                raise ValueError("请先在上方原图列表选择要批量填写的行")
            values = tuple(
                (field, MetadataCell(edit.text())) for field, edit in self.common.items()
            )
            proposal = MetadataPreview(
                metadata_digest(project),
                "共同值",
                tuple(
                    MetadataEntry(i + 1, row.filename, (row.row_id,), row.row_id, values)
                    for i, row in enumerate(project.rows)
                    if row.row_id in selected
                ),
            )
        self.show_preview(proposal, project)

    def show_preview(self, proposal: MetadataPreview, project: WBFigureProject) -> None:
        self.clear_preview()
        self.preview = proposal
        self._loading = True
        self.table.setRowCount(len(proposal.entries))
        self._target_model.clear()
        unbound = QStandardItem("未关联")
        unbound.setData("", Qt.ItemDataRole.UserRole)
        self._target_model.appendRow(unbound)
        for row in project.rows:
            target_item = QStandardItem(
                f"{row.filename} · {row.figure}/{row.protein} · {row.row_id[:8]}"
            )
            target_item.setData(row.row_id, Qt.ItemDataRole.UserRole)
            target_item.setToolTip(
                f"row_id={row.row_id}\nSHA256={row.source.sha256 if row.source else '缺图'}"
            )
            self._target_model.appendRow(target_item)
        for i, entry in enumerate(proposal.entries):
            check = QTableWidgetItem()
            check.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            check.setCheckState(Qt.CheckState.Unchecked)
            self.table.setItem(i, 0, check)
            key = QTableWidgetItem(f"{entry.line}: {entry.key}")
            key.setFlags(key.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 1, key)
            target = QComboBox()
            target.setModel(self._target_model)
            target.setCurrentIndex(max(0, target.findData(entry.target_id)))
            self._targets.append(target)
            self.table.setCellWidget(i, 2, target)
            values = dict(entry.values)
            for j, field in enumerate(METADATA_FIELDS, 3):
                cell = values.get(field, MetadataCell())
                item = QTableWidgetItem(cell.text)
                item.setData(Qt.ItemDataRole.UserRole, cell.error)
                item.setToolTip(cell.error or "空白保持原值")
                if cell.error:
                    item.setText(f"[{cell.error}]")
                self.table.setItem(i, j, item)
            issue = QTableWidgetItem(entry.issue or "唯一匹配；请核对后勾选")
            issue.setFlags(issue.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 10, issue)
        self._loading = False
        self.status.setText(f"预览 {len(proposal.entries)} 条；可修改值和目标行。尚未应用到项目。")
        self.status.setToolTip(proposal.source)

    def select_entries(self, checked: bool) -> None:
        for i in range(self.table.rowCount()):
            item = self.table.item(i, 0)
            if item is not None:
                item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)

    def _corrected(self, row: int, column: int) -> None:
        if self._loading or not 3 <= column <= 9:
            return
        item = self.table.item(row, column)
        if item is not None:
            self._loading = True
            item.setData(Qt.ItemDataRole.UserRole, "")
            item.setToolTip("已手动修改")
            self._loading = False

    def apply(self, project: WBFigureProject) -> WBFigureProject:
        if self.preview is None:
            raise ValueError("请先生成元信息预览")
        selected: list[MetadataEntry] = []
        for i, entry in enumerate(self.preview.entries):
            check = self.table.item(i, 0)
            if check is None or check.checkState() != Qt.CheckState.Checked:
                continue
            values: list[tuple[str, MetadataCell]] = []
            for j, field in enumerate(METADATA_FIELDS, 3):
                item = self.table.item(i, j)
                if item is not None:
                    values.append(
                        (
                            field,
                            MetadataCell(item.text(), item.data(Qt.ItemDataRole.UserRole) or ""),
                        )
                    )
            selected.append(
                replace(entry, target_id=self._targets[i].currentData(), values=tuple(values))
            )
        return apply_metadata(
            project,
            self.preview,
            tuple(selected),
            tuple(f for f, check in self.enabled.items() if check.isChecked()),
        )
