"""Current page, automatic raw crops, real workers, explicit identity and durable results."""

import csv
import json
from hashlib import sha256
from pathlib import Path
from typing import cast

import pytest
import tifffile
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtCore import QSettings
from pytestqt.qtbot import QtBot
from wb_tool.api import WBIntakeOutputProject, WBIntakeProject, WBNormalizedProject

from tests.test_intake_web_ui import javascript
from tooling.qt_test_lifecycle import close_and_dispose_window
from tools.wb.tests.test_source_geometry import membrane


@pytest.mark.parametrize("supported, guided", [(True, False), (True, True), (False, False)])
def test_automatic_batch_to_explicit_sample_results(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, supported: bool, guided: bool
) -> None:
    sources = tmp_path / "inputs"
    sources.mkdir()
    originals: dict[Path, str] = {}
    for index, name in enumerate(("A_123456 (1).tiff", "B_123456 (1).tiff")):
        pixels = membrane(marker=False)
        # The positive control supplies the instrument's signal/guide/merged trio.
        # The single-image control includes rail pixels and must remain invalid.
        if not supported:
            for center in (254, 302, 350, 398, 446):
                pixels[150, center] = 0
        arrays = [pixels]
        if guided:
            guide = membrane(marker=False)
            guide[guide > 15] = 50000
            signal = pixels.copy()
            signal[signal == 15] = 50000
            arrays = [signal, guide, pixels]
        for suffix, array in enumerate(arrays, 1):
            array[0, 0] += index  # Identity differs outside all band sampling areas.
            path = sources / name.replace("(1)", f"({suffix})")
            tifffile.imwrite(path, array)
            originals[path] = sha256(path.read_bytes()).hexdigest()
    settings = QSettings(str(tmp_path / "student.ini"), QSettings.Format.IniFormat)
    settings.setValue("project_parent", str(tmp_path / "projects"))
    settings.setValue(
        "workbench_appearance_v1",
        json.dumps(
            {
                "schema_version": 1,
                "values": {"theme": "forest", "density": "comfortable", "motion": "reduced"},
            }
        ),
    )
    window = WebWorkbenchWindow(settings=settings)
    window.show()
    host = window.host
    try:
        window.start_from_images([sources], intake=True)

        def imported() -> bool:
            p = host.view.project()
            return (
                isinstance(p, WBIntakeProject)
                and len(p.intake.sources) == (6 if guided else 2)
                and not host.operation_busy
            )

        qtbot.waitUntil(imported, timeout=20000)
        qtbot.waitUntil(
            lambda: (
                javascript(
                    window,
                    qtbot,
                    "!!document.querySelector('[data-group-action=add-fig]') &&"
                    "!document.querySelector('[data-group-action=add-fig]').disabled"
                    " && !state.busy",
                )
                is True
            )
        )
        assert (
            javascript(
                window,
                qtbot,
                """(()=>{
            const fill=(e,v)=>{e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}));};
            document.querySelector('[data-group-action=add-fig]').click();
            fill(document.querySelector('[data-group-field=fig-label]'),'Experiment');
            fill(document.querySelector('[data-group-field=lanes]'),'5');
            fill(document.querySelector('[data-group-field=proteins]'),'Target\\nReference');
            const choices=()=>[...document.querySelectorAll('[data-group-source]')];
            const names=[...new Set(choices().map(e=>e.name))];
            for(const name of names){choices().find(e=>e.name===name).click();}
            const start=document.querySelector('[data-group-action=start]');
            if(start.disabled)return false;start.click();return true;
        })()""",
            )
            is True
        )

        def processed() -> bool:
            p = host.view.project()
            return (
                isinstance(p, WBIntakeOutputProject)
                and bool(p.intake_outputs)
                and p.intake_outputs[-1].complete
                and not host.operation_busy
            )

        qtbot.waitUntil(processed, timeout=60000)
        original = host.view.project()
        assert isinstance(original, WBIntakeOutputProject)
        assert all(not row.reviewed for row in original.rows)
        assert all(
            plan.run and plan.run.state == "succeeded" and plan.run.pid
            for plan in original.analyses
        )
        run_ids = tuple(plan.run.run_id for plan in original.analyses if plan.run)
        output = Path(original.intake_outputs[-1].destination)
        archive = output / "项目恢复.zip"
        previous_archive = sha256(archive.read_bytes()).hexdigest()
        qtbot.waitUntil(
            lambda: javascript(window, qtbot, "!state.busy && !intakeWorkspace.hasDraft()") is True,
            timeout=10000,
        )
        javascript(window, qtbot, "switchMode('results');true")
        qtbot.waitUntil(
            lambda: (
                javascript(
                    window,
                    qtbot,
                    "!!document.querySelector('#intake-workspace [data-section=normalization]') &&"
                    "!document.querySelector('#intake-workspace [data-section=normalization]')"
                    ".disabled",
                )
                is True
            ),
            timeout=10000,
        )
        assert (
            javascript(
                window,
                qtbot,
                "switchMode('results');document.querySelector("
                "'#intake-workspace [data-section=normalization]').click();true",
            )
            is True
        )

        def ready() -> None:
            qtbot.waitUntil(
                lambda: (
                    javascript(
                        window,
                        qtbot,
                        "!!document.querySelector('#advanced-editor')&&!document.querySelector('#advanced-status').textContent.startsWith('正在')",
                    )
                    is True
                ),
                timeout=20000,
            )
            assert not javascript(
                window,
                qtbot,
                "document.querySelector('#advanced-status').classList.contains('advanced-error')",
            )

        def field(path: str, value: object) -> None:
            javascript(
                window,
                qtbot,
                "(()=>{const e=document.querySelector('[data-adv-path=\""
                + path
                + "\"]');e.value="
                + json.dumps(value)
                + ";e.dispatchEvent(new Event(e.tagName==='SELECT'?'change':'input',"
                "{bubbles:true}));})()",
            )

        def click(action: str) -> None:
            javascript(
                window,
                qtbot,
                "document.querySelector('[data-advanced=\"" + action + "\"]').click();true",
            )
            ready()

        ready()
        field("target", original.rows[0].row_id)
        field("reference", original.rows[1].row_id)
        field("kind", "housekeeping")
        click("normalization_create")
        for i in range(5):
            prefix = f"plans.0.pairs.{i}."
            for key, value in {
                "sample": f"sample-{i}",
                "reference_lane": i + 1,
                "identity.experiment_id": "experiment-1",
                "identity.group": "control" if i == 0 else "treated",
                "identity.biological_replicate": f"animal-{i}",
                "identity.technical_replicate": "measurement-1",
            }.items():
                field(prefix + key, value)
        field("plans.0.control_mode", "single_control")
        javascript(
            window,
            qtbot,
            "document.querySelector('[data-adv-path=\"plans.0.pairs.0.control\"]').click();document.querySelector('[data-adv-path=\"plans.0.confirmed\"]').click();true",
        )
        click("normalization_apply")
        click("tables_refresh")
        cells = cast(
            dict[str, list[dict[str, object]]],
            window.bridge.advanced_commands.tables["normalization"],
        )["cells"]
        assert len(cells) == 5
        if supported:
            assert all(c["ratio"] == 1 and c["relative"] == 1 for c in cells), cells
        else:
            assert all(c["ratio"] is None and c["relative"] is None for c in cells)
            assert all("dtype_min_present" in str(c["ratio_reason"]) for c in cells)
        assert all(c["identity_status"] == "specified" for c in cells)
        exported = tmp_path / "samples.csv"

        def destination(*_args: object, **_kwargs: object) -> tuple[str, str]:
            return str(exported), ""

        monkeypatch.setattr(
            "bioimage_app.web_advanced.QFileDialog.getSaveFileName",
            destination,
        )
        click("normalization_export")
        with exported.open(encoding="utf-8-sig", newline="") as stream:
            records = list(csv.DictReader(stream))
        assert len(records) == 5 and records[4]["生物重复 ID"] == "text:animal-4"
        # Like capture_workbench, settle compositor animations for static evidence.
        # All functional actions and assertions above ran with normal animations.
        javascript(window, qtbot, "document.getAnimations().forEach(a=>a.finish());true")
        qtbot.wait(350)
        assert javascript(
            window,
            qtbot,
            "getComputedStyle(document.querySelector('#drawer')).opacity==='1'",
        )
        assert window.grab().save(str(tmp_path / "student-results.png"))
        saved = host.view.project()
        assert isinstance(saved, WBNormalizedProject)
        javascript(window, qtbot, "closeDrawer();true")
        host.load_document(saved.project_id)
        qtbot.waitUntil(lambda: not host.operation_busy, timeout=20000)
        assert host.view.project() == saved
        assert tuple(plan.run.run_id for plan in saved.analyses if plan.run) == run_ids
        assert sha256(archive.read_bytes()).hexdigest() == previous_archive
        assert all(
            sha256(path.read_bytes()).hexdigest() == digest for path, digest in originals.items()
        )
        workspace = host.workspace_path
        javascript(window, qtbot, "switchMode('results');true")
        qtbot.waitUntil(lambda: window.navigation.read(workspace).get("mode") == "results")
        window.bridge.session("home", "{}")
        qtbot.waitUntil(lambda: window.host is not host, timeout=20000)
        host = window.host
        qtbot.waitUntil(lambda: window.shutdown_stage == "idle", timeout=20000)
        window.open_project(workspace)
        qtbot.waitUntil(
            lambda: (
                window.host.view.project().project_id == saved.project_id
                and not window.host.operation_busy
                and window.shutdown_stage == "idle"
            ),
            timeout=25000,
        )
        qtbot.waitUntil(lambda: javascript(window, qtbot, "mode") == "results", timeout=10000)
        assert window.host.view.project() == saved
        assert window.navigation.read(workspace)["mode"] == "results"
    finally:
        close_and_dispose_window(
            window, qtbot, resources_closed=lambda: host.resources_closed, timeout=20000
        )
