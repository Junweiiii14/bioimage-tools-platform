"""Build product wheels and exercise separate installed tool/runtime environments."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def installed_check(
    folder: Path,
    package: str,
    wheels: list[Path],
    script: str,
    extras: tuple[str, ...] = (),
) -> int:
    environment = folder / (package + "-".join(extras))
    code = subprocess.run(
        ["uv", "venv", "--python", sys.executable, str(environment)], cwd=ROOT, check=False
    ).returncode
    if code:
        return code
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    code = subprocess.run(
        [
            "uv",
            "sync",
            "--locked",
            "--package",
            package,
            "--no-dev",
            "--no-install-workspace",
            *(argument for extra in extras for argument in ("--extra", extra)),
        ],
        cwd=ROOT,
        env={
            **{key: value for key, value in os.environ.items() if key != "VIRTUAL_ENV"},
            "UV_PROJECT_ENVIRONMENT": str(environment),
        },
        check=False,
    ).returncode
    if code:
        return code
    code = subprocess.run(
        [
            "uv",
            "pip",
            "install",
            "--python",
            str(python),
            "--no-deps",
            *(str(wheel) for wheel in wheels),
        ],
        cwd=folder,
        check=False,
    ).returncode
    if code:
        return code
    return subprocess.run([str(python), "-I", "-c", script], cwd=folder, check=False).returncode


WB_SCRIPT = """
import sys
from pathlib import Path
from wb_tool.api import (
    AnalysisRequest, BandAnnotation, BandBounds, Baseline, LaneAnnotation, LaneROI,
    analyze_annotations, compute_lane_profiles, integrate_profile, load_tiff,
    StartFrame, WorkerConversation, encode_worker_frame, ResultFrame,
    CropRequest, export_crop, fixed_lane_grid,
)
import numpy as np
import tifffile
import subprocess
import wb_tool.api
assert Path(wb_tool.api.__file__).is_relative_to(Path(sys.prefix))
assert integrate_profile([10., 20., 10.], BandBounds(0, 2)).signal == 10.
assert integrate_profile([8., 8.], BandBounds(0, 1), Baseline(0, 0)).signal == 8.
pixels = np.array([[245], [235], [245]], dtype=np.uint8)
assert compute_lane_profiles(pixels, LaneROI('L', 0, 0, 1, 3), 'dark').quantitative == (10.,20.,10.)
tifffile.imwrite('analytic.tif', pixels)
image = load_tiff('analytic.tif')
assert len(fixed_lane_grid(LaneROI('G', 0, 0, 12, 3), 3)) == 3
export_crop('analytic.tif', CropRequest(image.sha256, 0, LaneROI('C', 0, 0, 1, 2)), 'crop.tif')
assert np.array_equal(load_tiff('crop.tif').pixels, pixels[:2])
lane = LaneAnnotation(LaneROI('L', 0, 0, 1, 3), (BandAnnotation('B', BandBounds(0, 2)),))
request = AnalysisRequest(image.sha256, 7, 'dark', (lane,))
result = analyze_annotations(image, request)
assert result.lanes[0].bands[0].signal == 10 and result.request.revision == 7
start = StartFrame(protocol_version=1, kind='start', sequence=0, run_id='r',
                  attempt_id='a', request_id='q', source_path=str(Path('analytic.tif').resolve()),
                  request=request)
worker = subprocess.run([sys.executable, '-I', '-m', 'wb_tool.worker'],
                        input=encode_worker_frame(start), capture_output=True, timeout=30)
assert worker.returncode == 0, worker.stderr
frames = worker.stdout.splitlines()
assert len(frames) == 3
session = WorkerConversation(start)
received = [session.accept(data) for data in frames]
assert isinstance(received[-1], ResultFrame)
assert received[-1].result.lanes[0].bands[0].signal == 10
assert not any(name.startswith(('PySide6', 'sqlite3')) for name in sys.modules)
assert not any(name.startswith(('rapidocr', 'onnxruntime', 'cv2')) for name in sys.modules)
print('Isolated WB wheel: TIFF/analysis, crop/grid and worker; no GUI/storage dependencies')
"""

RUNTIME_SCRIPT = """
import importlib.util
import os
import sys
import subprocess
from pathlib import Path
from hashlib import sha256
from platform_runtime.api import Workspace
from tool_contracts.api import ProcessExitReceipt
import platform_runtime.api
import tool_contracts.api
assert Path(platform_runtime.api.__file__).is_relative_to(Path(sys.prefix))
assert Path(tool_contracts.api.__file__).is_relative_to(Path(sys.prefix))
assert importlib.util.find_spec('wb_tool') is None
assert importlib.util.find_spec('numpy') is None
source = Path('asset.bin')
source.write_bytes(b'immutable input')
with Workspace.create('installed-workspace') as store:
    ref = store.import_asset(source, sha256(source.read_bytes()).hexdigest())
    assert store.read_asset(ref) == b'immutable input'
    store.save_draft('D', 'probe', 0, b'{}', expected_previous_revision=None)
    run = store.prepare_run('D')
    child = subprocess.Popen([sys.executable, '-I', '-c', 'pass'])
    store.start_run(run.run_id, child.pid)
    code = child.wait(timeout=10)
    completed = store.commit_result(run.run_id,
        ProcessExitReceipt(run_id=run.run_id, pid=child.pid, exit_code=code), b'{}')
    assert completed.state == 'succeeded'
with Workspace.open('installed-workspace') as store:
    assert store.get_run(run.run_id) == completed
assert not any(name.startswith(('wb_tool', 'PySide6', 'numpy')) for name in sys.modules)
print('Isolated runtime/contracts wheels: immutable input, run commit/reopen; no tool/GUI/numerics')
"""


GUI_SCRIPT = """
import sys
import subprocess
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from bioimage_app.api import create_wb_window, create_figure_project_window, DesktopDiagnostics
import bioimage_app.api
assert Path(bioimage_app.api.__file__).is_relative_to(Path(sys.prefix))
app = QApplication([])
diagnostics = DesktopDiagnostics(Path('installed-diagnostics'))
window = create_wb_window()
window.show()
assert window.isVisible() and window.view.canvas is not None
QTimer.singleShot(50, window.close)
QTimer.singleShot(10000, app.quit)
app.exec()
diagnostics.close()
assert 'session_end' in diagnostics.path.read_text(encoding='utf-8')
assert not window.isVisible()
project_window = create_figure_project_window()
project_window.show()
assert project_window.isVisible() and project_window.view.table.columnCount() == 11
QTimer.singleShot(50, project_window.close)
QTimer.singleShot(10000, app.quit)
app.exec()
assert project_window.resources_closed
worker = subprocess.run([sys.executable, '-I', '-m', 'bioimage_app', '--worker', 'wb'],
    input=b'{}\\n', capture_output=True, timeout=15)
assert worker.returncode == 2 and len(worker.stdout.splitlines()) == 2, worker
import numpy as np
import tifffile
from PIL import Image, ImageDraw, ImageFont
from wb_tool.api import recognize_figure, load_tiff, suggest_figures
figure = Image.new('L',(1200,500),245)
draw = ImageDraw.Draw(figure)
font = ImageFont.load_default(size=42)
draw.text((30,20),'Fig 1A',font=font,fill=0)
draw.text((30,150),'AKT',font=font,fill=0)
tifffile.imwrite('installed-fig.tif',np.array(figure))
source = load_tiff('installed-fig.tif')
from tool_contracts.api import AssetRef
from wb_tool.api import (FigureRow, FigureTemplate, FigureSourcePath, WBFigureProject,
    LaneROI, export_figure_bundle)
asset = AssetRef(asset_id='figure-source', relative_path='inputs/original.tif',
    sha256=source.sha256, size_bytes=Path('installed-fig.tif').stat().st_size)
row = FigureRow(row_id='row', source=asset, filename='original.tif', width=1200, height=500,
    bit_depth=8, figure='Fig1A', protein='AKT', lane_count=3,
    roi=LaneROI('row', 0, 100, 1200, 160), reviewed=True)
project = WBFigureProject(project_id='installed-project', rows=(row,), figure_order=('Fig1A',),
    template=FigureTemplate())
source_path = FigureSourcePath(source.sha256, str(Path('installed-fig.tif').resolve()))
export_figure_bundle(project, (source_path,),
    str(Path('installed-figure.zip').resolve()))
assert Path('installed-figure.zip').exists()
from wb_tool.api import (CropDetectionSettings, WBReviewProject, suggest_crops,
    record_crop_suggestion, read_figure_project)
suggestion = suggest_crops('installed-fig.tif', source.sha256, 'row', 0,
    CropDetectionSettings(3, 60, 'dark', left_marker=False,
        membrane_hint=LaneROI('membrane', 0, 0, 1200, 500)))
review_project = record_crop_suggestion(project, suggestion)
assert isinstance(review_project, WBReviewProject)
assert read_figure_project(review_project.model_dump_json().encode()) == review_project
assert review_project.rows[0].roi == row.roi
from wb_tool.api import (WBAnalysisProject, make_row_analysis, set_row_analysis,
    fill_project_table, export_project_table)
analysis_project = set_row_analysis(review_project,
    make_row_analysis(review_project, 'row', 'dark'))
assert isinstance(analysis_project, WBAnalysisProject)
assert read_figure_project(analysis_project.model_dump_json().encode()) == analysis_project
assert len(analysis_project.suggestions) == 1
assert all(cell.value is None for cell in fill_project_table(analysis_project, ()))
export_project_table(analysis_project, (), 'installed-project-results.xlsx')
assert Path('installed-project-results.xlsx').exists()
recognized = recognize_figure('installed-fig.tif',source.sha256)
groups = suggest_figures(recognized)
assert len(groups) == 1 and groups[0].heading.text == 'Fig 1A'
assert groups[0].rows[0].text == 'AKT'
from hashlib import sha256
from pydantic import TypeAdapter
from tool_contracts.api import RunRecord
from wb_tool.api import (OCRRecognition, ProjectOCRState, WBProjectOCR, project_with_ocr,
    read_project_ocr_result, install_project_recognition, bind_project_ocr_row,
    fill_project_ocr_table, export_project_ocr_table)
ocr_project = project_with_ocr(analysis_project,
    ProjectOCRState(source=asset, filename='installed-fig.tif', width=1200, height=500))
data = TypeAdapter(OCRRecognition).dump_json(recognized)
result_asset = AssetRef(asset_id='ocr-result', relative_path='results/ocr.json',
    sha256=sha256(data).hexdigest(), size_bytes=len(data))
request_data = ocr_project.model_dump_json().encode()
request_asset = AssetRef(asset_id='ocr-request', relative_path='requests/ocr.json',
    sha256=sha256(request_data).hexdigest(), size_bytes=len(request_data))
# Pure API fixture. Real run/commit orchestration is exercised by desktop integration tests.
run = RunRecord(run_id='ocr-fixture', document_id=project.project_id, tool_id='wb-figure',
    revision=0, state='succeeded', pid=123, request=request_asset, result=result_asset)
loaded_ocr = read_project_ocr_result(ocr_project, run, data)
ocr_project = install_project_recognition(ocr_project, loaded_ocr)
ocr_project = bind_project_ocr_row(ocr_project, ocr_project.ocr.rows[0].row_id, 'row')
assert isinstance(ocr_project, WBProjectOCR) and len(ocr_project.analyses) == 1
assert read_figure_project(ocr_project.model_dump_json().encode()) == ocr_project
assert all(c.status == 'unconfirmed' and c.value is None
    for c in fill_project_ocr_table(ocr_project, (), loaded_ocr))
export_project_ocr_table(ocr_project, (), loaded_ocr, 'installed-project-ocr.xlsx')
assert Path('installed-project-ocr.xlsx').exists()
print('Installed project v4: OCR evidence, explicit binding, roundtrip and literal XLSX passed')
from wb_tool.api import (WBNormalizedProject, make_normalization_plan,
    project_with_normalizations, fill_project_normalization, export_project_normalization)
reference = row.model_copy(update={'row_id': 'reference', 'protein': 'total AKT',
    'roi': LaneROI('reference', 0, 250, 1200, 310)})
paired_project = ocr_project.model_copy(update={'rows': (row, reference)})
plan = make_normalization_plan(paired_project, 'row', 'reference', 'phospho_total')
normalized = project_with_normalizations(paired_project, (plan,))
assert isinstance(normalized, WBNormalizedProject) and normalized.ocr == ocr_project.ocr
assert normalized.analyses == ocr_project.analyses
assert read_figure_project(normalized.model_dump_json().encode()) == normalized
assert all(c.ratio is None and c.ratio_status == 'pending_review'
    for c in fill_project_normalization(normalized, (), loaded_ocr).cells)
export_project_normalization(normalized, (), loaded_ocr, 'installed-normalization.xlsx')
assert Path('installed-normalization.xlsx').exists()
without_ocr = normalized.model_copy(update={'ocr': None})
assert read_figure_project(without_ocr.model_dump_json().encode()) == without_ocr
print('Installed project v5: explicit pairing, optional OCR, roundtrip and XLSX passed')
print('Installed WB desktop window: real widgets/entry assembly and async close passed')
print('Installed optional OCR: verified bundled PP-OCRv6 CPU recognition passed')
import subprocess
from wb_tool.api import OCRStartFrame, OCRRequest, OCRResultFrame, encode_ocr_frame, parse_ocr_frame
start = OCRStartFrame(protocol_version=1, kind='start', sequence=0,
    run_id='installed', attempt_id='installed', request_id='installed',
    source_path=str(Path('installed-fig.tif').resolve()),
    request=OCRRequest(source_sha256=source.sha256, revision=0))
process = subprocess.run([sys.executable, '-I', '-m', 'bioimage_app', '--worker', 'wb_ocr'],
    input=encode_ocr_frame(start), capture_output=True, timeout=30)
assert process.returncode == 0, process.stderr
frames = process.stdout.splitlines()
assert len(frames) == 3 and isinstance(parse_ocr_frame(frames[-1]), OCRResultFrame)
print('Installed OCR worker: real protocol, bundled models and static route passed')
"""


DESKTOP_SCRIPT = """
import sys
from pathlib import Path
from PySide6.QtCore import QCoreApplication, QTimer
from bioimage_app.api import AsyncStorage, StorageCommand, ProcessEvent, RunSession
from platform_runtime.api import Workspace
import bioimage_app.api
assert Path(bioimage_app.api.__file__).is_relative_to(Path(sys.prefix))
app = QCoreApplication([])
store = AsyncStorage()
replies = []
completions = []
sessions = []
class Codec:
    def __init__(self): self.stage = 0
    def accept(self, frame):
        kinds = ('hello', 'accepted', 'result')
        assert frame.decode() == kinds[self.stage]
        event = ProcessEvent(kinds[self.stage], b'{}')
        self.stage += 1
        return event
    def cancellation(self): return b'cancel\\n'
def received(reply):
    if reply.value is not None and getattr(reply.value, 'state', None) == 'prepared':
        session = RunSession(store, reply.value, Codec())
        sessions.append(session)
        def completed(result):
            completions.append(result)
            store.shutdown()
        session.completed.connect(completed)
        code = ("import sys; print('hello',flush=True); sys.stdin.buffer.readline(); "
                "print('accepted',flush=True); print('result',flush=True)")
        session.start((sys.executable, '-I', '-c', code), str(Path.cwd()), b'start\\n')
store.replied.connect(replies.append)
store.replied.connect(received)
store.closed.connect(app.quit)
store.submit(StorageCommand('create', path=str(Path('desktop-workspace').resolve())))
store.submit(StorageCommand('save', document_id='D', tool_id='probe', revision=0, data=b'{}'))
store.submit(StorageCommand('load', document_id='D'))
store.submit(StorageCommand('prepare', document_id='D'))
QTimer.singleShot(15000, app.quit)
app.exec()
assert len(replies) == 7 and all(reply.error_code is None for reply in replies), replies
assert replies[2].data == b'{}'
assert len(completions) == 1 and completions[0].record.state == 'succeeded', completions
with Workspace.open('desktop-workspace') as reopened:
    assert reopened.load_draft('D').revision == 0
assert not any(name.startswith(('wb_tool', 'numpy')) for name in sys.modules)
print('Isolated desktop wheel: Qt storage/process/terminal persistence; no experiment imports')
"""


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="bioimage-wheel-") as temporary:
        folder = Path(temporary)
        wheel_dir = folder / "wheels"
        packages = ("wb-tool", "tool-contracts", "platform-runtime", "bioimage-app")
        built: dict[str, Path] = {}
        for package in packages:
            code = subprocess.run(
                ["uv", "build", "--package", package, "--wheel", "--out-dir", str(wheel_dir)],
                cwd=ROOT,
                check=False,
            ).returncode
            if code:
                return code
            wheels = list(wheel_dir.glob(package.replace("-", "_") + "-*.whl"))
            if len(wheels) != 1:
                raise RuntimeError(f"Expected one built wheel for {package}")
            built[package] = wheels[0]
        for package, wheels, script in (
            (
                "platform-runtime",
                [built["tool-contracts"], built["platform-runtime"]],
                RUNTIME_SCRIPT,
            ),
            ("wb-tool", [built["tool-contracts"], built["wb-tool"]], WB_SCRIPT),
            (
                "bioimage-app",
                [built["tool-contracts"], built["platform-runtime"], built["bioimage-app"]],
                DESKTOP_SCRIPT,
            ),
        ):
            code = installed_check(folder, package, wheels, script)
            if code:
                return code
        return installed_check(
            folder,
            "bioimage-app",
            [
                built["tool-contracts"],
                built["platform-runtime"],
                built["wb-tool"],
                built["bioimage-app"],
            ],
            GUI_SCRIPT,
            ("wb",),
        )


if __name__ == "__main__":
    raise SystemExit(main())
