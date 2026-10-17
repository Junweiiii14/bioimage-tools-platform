"""Real Qt Widgets/QGraphicsView probe. Evidence labels measurement boundaries."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import numpy.typing as npt
from PySide6.QtCore import QPointF, Qt, QThread, QTimer, Signal
from PySide6.QtGui import (
    QCloseEvent,
    QColor,
    QImage,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from tooling.p0.controller import Controller
from tooling.p0.imaging import Pixels, digest, load, preview, profile
from tooling.p0.metrics import peak_memory, summary


class Loader(QThread):
    def __init__(self, path: Path, parent: QWidget) -> None:
        super().__init__(parent)
        self.path = path
        self.raw: Pixels | None = None
        self.display: npt.NDArray[np.uint8] | None = None
        self.sha = ""
        self.error = ""

    def run(self) -> None:
        try:
            self.raw = load(self.path)
            self.sha = digest(self.raw)
            self.display = preview(self.raw)
        except (ValueError, OSError, MemoryError) as exc:
            self.error = str(exc)


class Curve(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.values: npt.NDArray[np.float64] = np.array([], dtype=np.float64)
        self.setMinimumHeight(100)
        self.setMaximumHeight(145)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#101827"))
        painter.setPen(QPen(QColor("#5eead4"), 2))
        if self.values.size > 1:
            low, high = float(self.values.min()), float(self.values.max())
            spread = max(high - low, 1.0)
            previous = QPointF(0, self.height() - 10)
            for index, value in enumerate(self.values):
                point = QPointF(
                    index * (self.width() - 1) / (self.values.size - 1),
                    self.height() - 10 - (float(value) - low) / spread * (self.height() - 20),
                )
                if index:
                    painter.drawLine(previous, point)
                previous = point
        painter.end()


class Canvas(QGraphicsView):
    moved = Signal()

    def __init__(self, scene: QGraphicsScene, controller: Controller) -> None:
        super().__init__(scene)
        self.controller = controller
        self.pending: list[tuple[float, bool]] = []
        self.samples: list[float] = []
        self.busy_samples: list[float] = []
        self.setMinimumHeight(200)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        started = time.perf_counter()
        super().mouseMoveEvent(event)
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.pending.append((started, self.controller.busy))
            self.moved.emit()
            self.viewport().update()

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
        ended = time.perf_counter()
        for started, busy in self.pending:
            value = (ended - started) * 1000
            self.samples.append(value)
            if busy:
                self.busy_samples.append(value)
        self.pending.clear()


class Window(QWidget):
    def __init__(self, fixtures: Path, evidence: Path, started: float) -> None:
        super().__init__()
        self.setWindowTitle("Bioimage P0 — 本机技术验证")
        self.fixtures, self.evidence = fixtures, evidence
        self.started = started
        self.ready_seconds: float | None = None
        self.raw: Pixels | None = None
        self.raw_sha = ""
        self.loader: Loader | None = None
        self.roi: QGraphicsRectItem | None = None
        self.roi_box = (0, 0, 1, 1)
        self.closing = False
        self.controller = Controller(self)
        self.scene = QGraphicsScene(self)
        self.canvas = Canvas(self.scene, self.controller)
        self.curve = Curve()
        self.status = QLabel("就绪：请选择并载入合成样本")
        self.info = QLabel("原始图只读；曲线使用原始像素，RGB 使用红通道。ROI 半开区间。")
        self.choice = QComboBox()
        self.choice.addItems(["灰度2048.tif", "灰度4096.tif", "彩色4096.tif"])
        self.load_button = QPushButton("载入样本")
        self.load_button.clicked.connect(self.load_image)
        self.run_button = QPushButton("运行 20 图批次")
        self.run_button.clicked.connect(self.run_batch)
        self.cancel_button = QPushButton("取消任务")
        self.cancel_button.clicked.connect(self.controller.cancel)
        self.crash_button = QPushButton("模拟 worker 崩溃")
        self.crash_button.clicked.connect(self.crash)
        export = QPushButton("保存验证记录")
        export.clicked.connect(self.save_evidence)
        row = QHBoxLayout()
        for widget in (
            self.choice,
            self.load_button,
            self.run_button,
            self.cancel_button,
            self.crash_button,
            export,
        ):
            row.addWidget(widget)
        layout = QVBoxLayout(self)
        layout.addLayout(row)
        layout.addWidget(self.info)
        layout.addWidget(self.canvas, 1)
        layout.addWidget(self.curve)
        layout.addWidget(self.status)
        self.controller.changed.connect(self.status.setText)
        self.controller.changed.connect(self.buttons)
        self.controller.ended.connect(self.worker_ended)
        self.canvas.moved.connect(self.update_roi)
        self.timer = QTimer(self)
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.tick)
        self.last_tick = time.perf_counter()
        self.jitter: list[float] = []
        self.timer.start()
        self.resize(1000, 700)
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry()
        self.resize(min(1000, available.width() - 50), min(700, available.height() - 70))
        self.buttons()

    def buttons(self) -> None:
        self.run_button.setEnabled(not self.controller.busy)
        self.crash_button.setEnabled(not self.controller.busy)
        self.cancel_button.setEnabled(self.controller.busy)

    def tick(self) -> None:
        now = time.perf_counter()
        if self.controller.busy:
            self.jitter.append(max(0, (now - self.last_tick) * 1000 - 20))
        self.last_tick = now
        if self.ready_seconds is None and self.isVisible():
            self.ready_seconds = now - self.started

    def load_image(self) -> None:
        if self.loader is not None:
            return
        self.loader = Loader(self.fixtures / self.choice.currentText(), self)
        self.loader.finished.connect(self.image_loaded)
        self.load_button.setEnabled(False)
        self.status.setText("载入中")
        self.loader.start()

    def image_loaded(self) -> None:
        loader = self.loader
        if loader is None:
            return
        if loader.raw is None or loader.display is None or loader.error:
            self.status.setText(f"载入失败：{loader.error}")
        else:
            self.raw, self.raw_sha = loader.raw, loader.sha
            display = loader.display
            height, width = display.shape[:2]
            fmt = (
                QImage.Format.Format_Grayscale8
                if display.ndim == 2
                else QImage.Format.Format_RGB888
            )
            image = QImage(display.data, width, height, display.strides[0], fmt).copy()
            self.scene.clear()
            self.scene.addPixmap(QPixmap.fromImage(image))
            self.scene.setSceneRect(0, 0, width, height)
            self.roi = QGraphicsRectItem(0, 0, min(512, width), min(512, height))
            self.roi.setPen(QPen(QColor("#f43f5e"), 10))
            self.roi.setBrush(QColor(255, 100, 100, 45))
            self.roi.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
            self.roi.setPos(width // 3, height // 3)
            self.scene.addItem(self.roi)
            self.canvas.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self.update_roi()
            self.status.setText(f"已载入 {loader.path.name}；拖动红色 ROI")
        loader.deleteLater()
        self.loader = None
        self.load_button.setEnabled(True)
        if self.closing and not self.controller.busy:
            self.close()

    def update_roi(self) -> None:
        if self.roi is None or self.raw is None:
            return
        width, height = int(self.roi.rect().width()), int(self.roi.rect().height())
        x = max(0, min(round(self.roi.x()), self.raw.shape[1] - width))
        y = max(0, min(round(self.roi.y()), self.raw.shape[0] - height))
        self.roi.setPos(x, y)
        self.roi_box = (x, y, width, height)
        self.curve.values = profile(self.raw, self.roi_box)
        self.curve.update()
        self.info.setText(
            f"原始 {self.raw.dtype} {self.raw.shape} | ROI x={x} y={y} {width}×{height} | "
            f"剖面均值 {float(self.curve.values.mean()):.2f}（RGB 仅红通道）"
        )

    def run_batch(self) -> None:
        self.controller.start([self.fixtures / f"批次{i:02d}.tif" for i in range(20)])

    def crash(self) -> None:
        self.controller.start([self.fixtures / "灰度2048.tif"], mode="crash")

    def worker_ended(self) -> None:
        self.buttons()
        if self.closing and self.loader is None:
            self.close()

    def save_evidence(self) -> None:
        self.evidence.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        path = self.evidence / f"desktop-{stamp}.json"
        record = {
            "schema": 1,
            "timestamp": stamp,
            "startup_to_visible_event_seconds": self.ready_seconds,
            "executable": sys.executable,
            "entry": sys.argv[0],
            "cwd": str(Path.cwd()),
            "qt_platform": QApplication.platformName(),
            "device_pixel_ratio": self.devicePixelRatioF(),
            "QT_SCALE_FACTOR": os.environ.get("QT_SCALE_FACTOR"),
            "logical_window": [self.width(), self.height()],
            "raw_sha256_before": self.raw_sha,
            "raw_sha256_after": digest(self.raw) if self.raw is not None else None,
            "roi": self.roi_box,
            "gui_peak_rss_bytes": peak_memory(),
            "measurement": (
                "Qt mouseMove handler entry to canvas paint completion; "
                "excludes OS input and physical display latency"
            ),
            "input_source": "native UI automation unless test runner specifies otherwise",
            "roi_ms": summary(self.canvas.samples),
            "roi_during_worker_ms": summary(self.canvas.busy_samples),
            "roi_during_worker_samples_ms": self.canvas.busy_samples,
            "event_loop_delay_during_worker_ms": summary(self.jitter),
            "runs": self.controller.history,
            "module_paths": {
                name: str(getattr(module, "__file__", ""))
                for name, module in sys.modules.copy().items()
                if name in {"numpy", "PySide6", "tifffile", "pydantic"}
            },
        }
        with path.open("x", encoding="utf-8") as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2)
        self.status.setText(f"记录已保存：{path.name}")

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.controller.busy or self.loader is not None:
            self.closing = True
            self.controller.cancel()
            event.ignore()
        else:
            event.accept()


def main(started: float) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    app = QApplication(sys.argv[:1])
    window = Window(args.fixtures.resolve(), args.evidence.resolve(), started)
    window.show()
    return app.exec()
