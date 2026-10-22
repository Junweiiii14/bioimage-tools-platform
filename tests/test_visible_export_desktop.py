"""Explorer-style drop → unreviewed real workers → visible table → XLSX/CSV files."""

import csv
import json
import os
from io import StringIO
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest
import tifffile
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QFileDialog
from pytestqt.qtbot import QtBot
from wb_tool.api import WBIntakeOutputProject

from tests.test_folder_drop import drop_window as drop_window
from tests.test_folder_drop import native_drop
from tests.test_instrument_intake_desktop import current, wait_saved
from tests.test_intake_web_ui import javascript
from tools.wb.tests.test_source_geometry import membrane

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def capture_frame(window: WebWorkbenchWindow, qtbot: QtBot, destination: Path) -> None:
    javascript(window, qtbot, "document.getAnimations().forEach(a=>a.finish());true")
    qtbot.wait(300)  # Wait for the settled compositor frame, not only the JS callback.
    assert window.web.grab().save(str(destination))


def test_real_unreviewed_result_matches_both_exports(
    drop_window: WebWorkbenchWindow,
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = drop_window
    root = tmp_path / "safe-synthetic-originals"
    root.mkdir()
    for i, angle in enumerate((3, -3), 1):
        raw_source = membrane(angle=angle, marker=False)
        raw_source[raw_source == 20000] = 0  # Deliberate dtype-rail quality-review fixture.
        tifffile.imwrite(root / f"Sample{i}_123456 (1).tiff", raw_source)
    originals = {p: p.read_bytes() for p in root.iterdir()}
    capture = os.environ.get("T077_EVIDENCE")
    if capture:
        Path(capture).mkdir(parents=True, exist_ok=True)
        capture_frame(window, qtbot, Path(capture) / "platform-1440.png")
        window.resize(960, 640)
        qtbot.waitUntil(lambda: javascript(window, qtbot, "innerWidth<=960") is True)
        capture_frame(window, qtbot, Path(capture) / "platform-960.png")
        window.resize(1440, 940)
    native_drop(window, qtbot, [QUrl.fromLocalFile(str(root))])
    qtbot.waitUntil(
        lambda: window.shutdown_stage == "idle" and bool(window.host.workspace_path), timeout=20000
    )
    wait_saved(window, qtbot)
    qtbot.waitUntil(
        lambda: (
            javascript(
                window,
                qtbot,
                "!!document.querySelector('[data-group-action=add-fig]')&&!state.busy",
            )
            is True
        )
    )
    javascript(
        window,
        qtbot,
        """
      const fill=(el,v)=>{el.value=v;el.dispatchEvent(new Event('input',{bubbles:true}));};
      for(let i=0;i<2;i++){
        document.querySelector('[data-group-action=add-fig]').click();
        fill(document.querySelectorAll('[data-group-field=fig-label]')[i],'Fig '+(i+1));
        fill(document.querySelectorAll('[data-group-field=lanes]')[i],'5');
        fill(document.querySelectorAll('[data-group-field=proteins]')[i],'AKT');
      }
      document.querySelectorAll('[data-group-source]')[0].click();
      document.querySelectorAll('[data-group-source]')[1].click();
      document.querySelector('[data-group-action=start]').click();true
    """,
    )
    qtbot.waitUntil(
        lambda: window.bridge.sequence_response.get("status") == "started", timeout=10000
    )

    def complete() -> bool:
        project = current(window)
        return isinstance(project, WBIntakeOutputProject) and all(
            s.status == "done" for s in project.workflow.steps
        )

    qtbot.waitUntil(complete, timeout=60000)
    wait_saved(window, qtbot)
    project = current(window)
    assert isinstance(project, WBIntakeOutputProject)
    assert all(not row.reviewed for row in project.rows)
    qtbot.waitUntil(
        lambda: (
            javascript(
                window,
                qtbot,
                "mode==='results'&&!!state.intake.visibleTable&&"
                "document.querySelector('.results-scroll table')?.checkVisibility()",
            )
            is True
        )
    )
    raw = javascript(
        window,
        qtbot,
        "JSON.stringify([...document.querySelectorAll("
        "'.intake-result-grid .results-scroll table tr')]"
        ".map(r=>[...r.children].map(c=>c.textContent.trim())))",
    )
    assert isinstance(raw, str)
    visible = json.loads(raw)
    assert len(visible) == 3 and any("*" in value for row in visible[1:] for value in row[2:-1])
    cells = window.host.view.analysis.result_view.cells
    assert any(c.raw_integral is not None and c.value is None for c in cells)
    original_zip = Path(project.intake_outputs[-1].destination, "project.zip").read_bytes()
    for suffix in ("xlsx", "csv"):
        destination = tmp_path / ("visible." + suffix)

        def choose_destination(
            *args: object, dest: Path = destination, **kwargs: object
        ) -> tuple[str, str]:
            return str(dest), ""

        monkeypatch.setattr(QFileDialog, "getSaveFileName", choose_destination)
        qtbot.waitUntil(
            lambda: (
                javascript(
                    window,
                    qtbot,
                    "!state.busy&&!intakeWorkspace.hasDraft()&&"
                    "!document.querySelector('[data-intake-table-export]').disabled",
                )
                is True
            ),
            timeout=10000,
        )
        javascript(
            window, qtbot, "document.querySelector('[data-intake-table-export]').click();true"
        )
        qtbot.waitUntil(
            lambda dest=destination: (
                not window.host.operation_busy
                and (dest.is_file() or window.host.view.status.text().startswith("操作失败"))
            ),
            timeout=20000,
        )
        assert destination.is_file(), (
            window.host.view.status.text(),
            window.bridge.snapshot().get("error"),
        )
        assert "已导出" in window.host.view.status.text()
        qtbot.waitUntil(
            lambda: (
                javascript(window, qtbot, "!state.busy&&state.cells.some(c=>c.rawIntegral!=null)")
                is True
            )
        )
        if suffix == "xlsx":
            with ZipFile(destination) as book:
                sheet = ET.fromstring(book.read("xl/worksheets/sheet1.xml"))
                exported: list[list[str]] = []
                for row in sheet.findall(f"{NS}sheetData/{NS}row"):
                    values: list[str] = []
                    for cell in row:
                        v = cell.findtext(f"{NS}v")
                        values.append(
                            (
                                f"{float(v):,.2f}".rstrip("0").rstrip(".")
                                + ("*" if cell.get("s") == "3" else "")
                            )
                            if v is not None
                            else cell.findtext(f"{NS}is/{NS}t", "")
                        )
                    exported.append(values)
                assert exported == visible
                assert b'numFmtId="165"' in book.read("xl/styles.xml")
                numeric = [
                    float(c.findtext(f"{NS}v", "nan"))
                    for c in sheet.iter(f"{NS}c")
                    if c.find(f"{NS}v") is not None
                ]
                assert numeric == [c.raw_integral for c in cells if c.raw_integral is not None]
        else:
            rows = list(csv.reader(StringIO(destination.read_text(encoding="utf-8-sig"))))
            assert [[v.removeprefix("text:") for v in row] for row in rows] == visible
        if capture:
            (Path(capture) / destination.name).write_bytes(destination.read_bytes())
    assert {p: p.read_bytes() for p in root.iterdir()} == originals
    assert Path(project.intake_outputs[-1].destination, "project.zip").read_bytes() == original_zip
    if capture:
        qtbot.waitUntil(
            lambda: (
                javascript(window, qtbot, "!state.busy&&state.cells.some(c=>c.rawIntegral!=null)")
                is True
            )
        )
        capture_frame(window, qtbot, Path(capture) / "results-1440.png")
        window.resize(960, 640)
        qtbot.waitUntil(lambda: javascript(window, qtbot, "innerWidth<=960") is True)
        capture_frame(window, qtbot, Path(capture) / "results-960.png")
        (Path(capture) / "visible.json").write_text(
            json.dumps(visible, ensure_ascii=False), encoding="utf-8"
        )
