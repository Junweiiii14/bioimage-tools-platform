"""Visible controls for the same finite workflow used by the command-line adapter."""

from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QStandardPaths, Qt, QUrl
from PySide6.QtGui import QCloseEvent, QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from bioimage_app.wb_workflow_host import wb_workflow_registry
from bioimage_app.workflow_input import prepare_wb_workspace
from bioimage_app.workflow_session import WorkflowSession, WorkflowStatus

_STATES = {
    "preparing": "准备输入",
    "running": "运行中",
    "pausing": "当前步骤完成后暂停",
    "paused": "已暂停，可继续",
    "cancelling": "正在取消并等待进程退出",
    "cancelled": "已取消",
    "succeeded": "已提交全部成果",
    "failed": "执行失败，可重开后重试",
    "interrupted": "执行中断，可重开后恢复",
}


class WorkflowWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("工作流执行 · BioImage")
        self.resize(960, 780)
        self._session: WorkflowSession | None = None
        self._session_closed = True
        self._closing = False
        self._workspace = Path()
        self._pending_rerun: tuple[str, str, str] | None = None
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)
        title = QLabel("原图 → 定量 → 成果")
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: #203b2e")
        layout.addWidget(title)
        note = QLabel("WB 原始整数图工作流。可靠步骤自动继续；暂停在步骤边界生效。")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.inputs = QWidget()
        form = QFormLayout(self.inputs)
        form.setContentsMargins(0, 0, 0, 0)
        self.mode = QComboBox()
        self.mode.addItem("处理真实原图", "")
        self.mode.addItem("合成验证：16 位三角信号", "triangle_u16")
        self.mode.addItem("合成验证：真实零值", "flat_zero")
        form.addRow("输入方式", self.mode)
        self.source = QLineEdit()
        self.parameters = QLineEdit()
        self.location = QLineEdit(
            str(
                Path(
                    QStandardPaths.writableLocation(
                        QStandardPaths.StandardLocation.DocumentsLocation
                    )
                )
                / "BioImage"
                / "Workflows"
                / uuid4().hex
            )
        )
        for label, field, filters in (
            ("原始 TIFF", self.source, "TIFF (*.tif *.tiff)"),
            ("分析参数", self.parameters, "分析参数 (*.json)"),
        ):
            row = QHBoxLayout()
            row.addWidget(field, 1)
            choose = QPushButton("选择…")
            choose.clicked.connect(lambda _checked=False, f=field, t=filters: self._choose(f, t))
            row.addWidget(choose)
            form.addRow(label, row)
        self.parameters.setPlaceholderText("现有 AnalysisRequest JSON；不猜测泳道或科学参数")
        form.addRow("工作区路径", self.location)
        self.execution = QLineEdit()
        self.execution.setPlaceholderText("新运行后自动显示；重开时使用原执行编号")
        form.addRow("执行编号", self.execution)
        self.report_layout = QComboBox()
        self.report_layout.addItem("舒展", "comfortable")
        self.report_layout.addItem("紧凑", "compact")
        form.addRow("报告排版", self.report_layout)
        layout.addWidget(self.inputs)
        actions = QHBoxLayout()
        self.start_button = QPushButton("开始新运行")
        self.open_button = QPushButton("重开此执行")
        self.pause_button = QPushButton("暂停")
        self.resume_button = QPushButton("继续 / 重试")
        self.apply_button = QPushButton("应用调整并运行")
        self.cancel_button = QPushButton("取消运行")
        for button in (
            self.start_button,
            self.open_button,
            self.pause_button,
            self.resume_button,
            self.apply_button,
            self.cancel_button,
        ):
            button.setMinimumHeight(36)
            actions.addWidget(button)
        layout.addLayout(actions)
        self.start_button.clicked.connect(self._start)
        self.open_button.clicked.connect(self._reopen)
        self.pause_button.clicked.connect(self._pause)
        self.resume_button.clicked.connect(self._resume)
        self.apply_button.clicked.connect(self._rerun)
        self.cancel_button.clicked.connect(self._cancel)
        self.summary = QLabel("选择原图和参数，或使用明确标记的合成验证输入。")
        self.summary.setWordWrap(True)
        self.summary.setTextFormat(Qt.TextFormat.PlainText)
        self.summary.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.summary)
        self.progress = QProgressBar()
        self.progress.setRange(0, 3)
        self.progress.setValue(0)
        self.progress.setFormat("已提交 %v / %m 步")
        layout.addWidget(self.progress)
        self.steps = QTreeWidget()
        self.steps.setHeaderLabels(["步骤", "状态", "真实运行编号"])
        self.steps.setRootIsDecorated(False)
        self.steps.setMinimumHeight(130)
        layout.addWidget(self.steps)
        self.outputs = QTreeWidget()
        self.outputs.setHeaderLabels(["已提交成果（双击打开）", "文件位置"])
        self.outputs.setRootIsDecorated(False)
        self.outputs.itemDoubleClicked.connect(self._open_output)
        layout.addWidget(self.outputs, 1)
        self.setCentralWidget(body)
        self.setStyleSheet(
            "QWidget { font-size: 14px; color: #203b2e; }"
            "QMainWindow { background: #f1f3e9; color: #203b2e; }"
            "QLabel { color: #203b2e; }"
            "QLineEdit, QComboBox, QTreeWidget { background: #fefff9; padding: 6px; }"
            "QPushButton { padding: 6px 12px; background: #fefff9; border: 1px solid #52634c; }"
            "QPushButton:hover { background: #e6efcf; }"
            "QPushButton:disabled { color: #52634c; background: #e9efde; border-color: #dce3d4; }"
            "QHeaderView::section { background: #e9efde; color: #203b2e; padding: 6px; }"
            "QProgressBar { background: #fefff9; border: 1px solid #dce3d4; "
            "min-height: 24px; text-align: center; }"
            "QProgressBar::chunk { background: #d7ed82; }"
        )
        self._buttons()

    def _choose(self, field: QLineEdit, filters: str) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "选择文件", "", filters)
        if filename:
            field.setText(filename)

    def _new_session(self) -> WorkflowSession:
        if self._session is not None:
            self._session.deleteLater()
        session = WorkflowSession(wb_workflow_registry, self)
        self._session, self._session_closed = session, False
        session.changed.connect(self._changed)
        session.completed.connect(self._completed)
        session.finished.connect(self._finished)
        self._workspace = Path(self.location.text()).resolve()
        self.steps.clear()
        self.outputs.clear()
        self.progress.setValue(0)
        self._buttons()
        return session

    def _start(self) -> None:
        validation = str(self.mode.currentData())
        source, parameters = self.source.text().strip(), self.parameters.text().strip()
        if not self.location.text().strip() or (not validation and (not source or not parameters)):
            self.summary.setText("请填写新工作区路径，并选择原图和分析参数，或选择合成验证。")
            return
        session = self._new_session()
        workspace, report_layout = self._workspace, str(self.report_layout.currentData())
        self.summary.setText("正在后台准备输入；原图与历史成果不会被覆盖。")
        session.initialize(
            str(workspace),
            lambda: prepare_wb_workspace(
                workspace,
                source_path=source,
                parameters=parameters,
                validation=validation,
                layout=report_layout,
            ),
        )
        self.execution.setText(session.status().execution_id)

    def _reopen(self) -> None:
        execution_id = self.execution.text().strip()
        if not self.location.text().strip() or not execution_id:
            self.summary.setText("请填写已有工作区路径和执行编号。")
            return
        self._new_session().reopen(str(self._workspace), execution_id)

    def _pause(self) -> None:
        assert self._session is not None
        self._session.pause()

    def _rerun(self) -> None:
        self._pending_rerun = (
            self.execution.text().strip(),
            self.parameters.text().strip(),
            str(self.report_layout.currentData()),
        )
        if self._session_closed:
            self._apply_adjustment()
        else:
            assert self._session is not None
            self._buttons()
            self._session.close()

    def _apply_adjustment(self) -> None:
        assert self._pending_rerun is not None
        execution_id, parameters, report_layout = self._pending_rerun
        self._pending_rerun = None
        session = self._new_session()
        workspace = self._workspace
        session.initialize(
            str(workspace),
            lambda: prepare_wb_workspace(
                workspace, rerun=execution_id, parameters=parameters, layout=report_layout
            ),
            cache_execution_id=execution_id,
        )
        self.execution.setText(session.status().execution_id)

    def _resume(self) -> None:
        assert self._session is not None
        self._session.resume()

    def _cancel(self) -> None:
        assert self._session is not None
        self._session.cancel()

    def _buttons(self) -> None:
        session = self._session
        ledger = session.ledger if session else None
        live = session is not None and not self._session_closed and not self._closing
        paused = ledger is not None and ledger.state == "paused"
        adjusting = self._pending_rerun is not None
        self.inputs.setEnabled((not live or paused) and not self._closing and not adjusting)
        for field in (self.source, self.location, self.execution, self.mode):
            field.setEnabled(not live)
        self.start_button.setEnabled(self._session_closed and not self._closing)
        self.open_button.setEnabled(self._session_closed and not self._closing)
        self.pause_button.setEnabled(live and ledger is not None and ledger.state == "running")
        self.resume_button.setEnabled(
            live
            and ledger is not None
            and ledger.active_attempt is None
            and ledger.state in ("running", "paused", "failed", "interrupted")
        )
        self.apply_button.setEnabled(
            ledger is not None
            and (paused or self._session_closed)
            and not self._closing
            and not adjusting
        )
        self.cancel_button.setEnabled(
            live and (ledger is None or ledger.state in ("running", "pausing", "paused"))
        )

    def _changed(self, status: WorkflowStatus) -> None:
        assert self._session is not None
        ledger = self._session.ledger
        message = status.message or _STATES.get(status.state, status.state)
        if (
            ledger
            and ledger.state == "succeeded"
            and any(r.quality == "issues" for r in ledger.results)
        ):
            message += "；部分数据需复核，请查看状态表"
        self.summary.setText(f"{message} · 复用 {status.reused_nodes} 步")
        self.progress.setMaximum(status.total_nodes or 3)
        self.progress.setValue(status.completed_nodes)
        self.steps.clear()
        self.outputs.clear()
        if ledger is not None:
            selected = {result.node_id: result for result in ledger.results}
            for node in ledger.plan.nodes:
                result = selected.get(node.node_id)
                attempt = next(
                    (a for a in reversed(ledger.attempts) if a.node_id == node.node_id), None
                )
                run = result.run if result else (attempt.run if attempt else None)
                state = (
                    ("复用已提交成果" if result.reused else "已提交")
                    if result
                    else (
                        "等待成果登记"
                        if run and run.state == "succeeded"
                        else _STATES.get(run.state, run.state)
                        if run
                        else "准备中"
                        if attempt and attempt.active
                        else "已终止"
                        if attempt
                        else "等待"
                    )
                )
                row = QTreeWidgetItem([node.node_id, state, run.run_id if run else ""])
                self.steps.addTopLevelItem(row)
            for output in ledger.plan.outputs:
                if output.node_id in selected:
                    ref = next(
                        item.asset
                        for item in selected[output.node_id].outputs
                        if item.port == output.port
                    )
                    self.outputs.addTopLevelItem(
                        QTreeWidgetItem([output.name, str(self._workspace / ref.relative_path)])
                    )
        self.steps.resizeColumnToContents(0)
        self.steps.resizeColumnToContents(1)
        self.outputs.resizeColumnToContents(0)
        self._buttons()

    def _completed(self, status: WorkflowStatus) -> None:
        self._changed(status)
        assert self._session is not None
        self._session.close()

    def _finished(self, status: WorkflowStatus) -> None:
        self._session_closed = True
        self._changed(status)
        if self._closing:
            self.close()
        elif self._pending_rerun is not None:
            self._apply_adjustment()

    def _open_output(self, item: QTreeWidgetItem, _column: int) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(item.text(1)))

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._session is not None and not self._session_closed:
            event.ignore()
            self._closing = True
            self.summary.setText("正在安全关闭，等待实际进程与存储退出…")
            self._buttons()
            self._session.close()
        else:
            event.accept()
