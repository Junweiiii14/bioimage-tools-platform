T077：平台 WB 入口支持本机目录原生拖入，复用新建仪器项目及草稿保护；最终结果页导出共用可见宽表，保存后重建结果展示。契约见 docs/contracts/wb-visible-result-table-v1.md。

T079：`--laboratory` 生成独立实验室离线发行，通道 `wb-laboratory`、设置 `Laboratory`；只改包装标题/身份，不改计算或项目格式。安装、目标机范围与清理证据见 T079 任务；诊断契约见 `docs/contracts/wb-installed-diagnostics-v1.md`。

T075网页与HTML预览共用web_ui资源。appearance@1按发行通道保存；web_advanced通过公开WB用例及宿主后台CAS处理四类高级工具，保留原桌面兼容入口。独立--ui-system-test候选不覆盖旧安装。验收状态见T075。

T061新增“识别导出组与条带”后台动作和集中复核；候选不自动填N或确认目标，保存重开保留证据。新测试候选显示为“图像识别测试版”，旧测试安装按用户授权在新版本首次启动前清理；实验项目/原图/历史结果不删。

E5/schema14 now freezes assets and run evidence, fills stable Fig/row/slot tables, writes
new output roots and imports the verified index before committing done. Reopening and
archive recovery retain imported history rather than inventing local runs. E6 reuses
same-operation frozen full renders, keeps original pixels separate and paginates all
stages. See T058/T059 for actual checks and remaining scientific/target-machine gaps.

E7 adds an explicit --execution-test builder profile with its own E7Test settings,
AppId, Chinese install directory and shortcuts; existing profiles remain separate.
--verify-intake-installation complements the independent grayscale/OCR diagnostic.
T060 records passed local Win11 installed dual-flow/lifecycle evidence for e579;
Product PR17 passed both910-case platform gates and merged to main; external
scientific/clean-target/DPI acceptance remains pending. Interface:
../../docs/contracts/wb-installed-diagnostics-v1.md.
E4 adds schema13 complete-Fig evidence and original-pixel measurement to intake.
IntakeWorkflowSession saves the complete Fig before starting its real RunSession batch;
deferred installation merges only verified committed results with the terminal stage.
Saved PNG previews use separate bounded display transforms and keep original source ROIs.
Results and per-Fig source links retain stable row identities, including duplicate labels;
measurement pages expose every fixed slot in batches of 200. Export-stage integration completed in E5; actual final status is recorded in T058. See T-057 and `../../docs/contracts/wb-intake-figure-v1.md` for actual checks
and limits; this is a Windows desktop workflow, not a standalone mobile web delivery.

E3 adds schema12 fixed-N crop review to the existing intake page. IntakeWorkflowSession
persists each owned claim before its WBBackground job, imports a verified original-value
TIFF from its owned temporary directory, and installs the terminal state by guarded CAS.
Uncertain detection keeps every planned slot and requires original-coordinate review;
no measurement is started. Same-project channel updates retain the review page and local
geometry drafts; failed saves retain drafts, and session changes retire them. See
`../../docs/contracts/wb-intake-crop-v1.md` and T-056 for evidence and remaining limits.

# Desktop host

T072 connects `intake_crop@2` machine acceptance and existing small-angle display frames
to unattended batches. The quantification page uses bounded, identity-checked saved Fig
previews independent of batch execution keys. Unified results expose the actual table
and direct Excel/CSV export. `--automatic-flow-test` builds a separate AutomaticFlowTest
distribution; `--verify-automatic-flow-installation <new-report.json>` checks reliable
two-Fig geometry without crop confirmations, original samples, visible images/regions,
results, real workers and reopening. This remains engineering evidence; see T072.

T071 adds the versioned Fig sequence editor and a single guarded start/continue
path. New batches use `intake_workflow@3`: all crops, then all complete Figs,
then original-pixel measurements, then a committed output. The live batch snapshot
drives page navigation; drafts, IME, dialogs and explicit browsing protect focus.
`--fig-sequence-test` builds an isolated FigSequenceTest distribution, preserving
GroupedIntakeTest. `--verify-sequence-installation <new-report.json>` operates the
shipped two-Fig page, reviews both crops and checks real workers, stage barriers,
navigation, output, reopening and owned shutdown. This synthetic diagnostic is
engineering evidence; actual T071 acceptance remains in its task/evidence files.

T069 adds `--grouped-intake-test`, an isolated GroupedIntakeTest distribution with
its own AppId, settings, Chinese install directory and shortcuts. The explicit
`--verify-grouped-intake-installation <new-report.json>` reuses the real intake
worker/output/reopen diagnostic after incomplete/complete group drafts and verifies
the shipped configurable shortcut settings. Old diagnostics/distributions remain
separate. Multi-root intake assigns each file to its selected root before beginning
the operation, preserving batch identity and rejecting outside-root paths. Actual
candidate acceptance and remaining target-machine/scientific gaps are in T069.

T066使用固定动作目录和当前发行通道QSettings提供可配置快捷键；文件菜单可进入设置，键盘与按钮共用操作，保护输入/IME/弹窗/忙态。详情 `../../docs/contracts/workbench-shortcuts-v1.md`，不改变科学数据或原灰度/OCR能力。

T065网格增加目标区域选择及原坐标显示框；已完成裁剪可明确保存修正，宿主CAS生成新修订，所属Fig当前结果失效、旧输出显示为历史。见 `../../docs/contracts/wb-intake-revision-v1.md`，不覆写原图或发布目录。

T064增加已批准的采集组网格：组内图并排、批量归Fig、组蛋白名、单选裁剪源和Fig级N，保存通过当前项目CAS；历史行式项目保留原界面。大图预览独立后台读取原图，显示数据不入定量。契约与状态见 `../../docs/contracts/wb-intake-grouping-v1.md` / T064。

E2 adds asynchronous execution-plan preparation after intake confirmation. Schema11
persists the stage ledger, while the web page shows the summary and explicit pending
states. Preparation is installed only after a successful normal save; cancellation
or a stale generation rejects its callback. Reopening interrupts unknown running
stages and requires approval again. Unused preparation can return to schema10 for
editing. Actual crop execution is connected in E3; this stage creates no measurements.

T051 adds a separate instrument-folder intake page. All supported raw TIFF candidates
retain their original names and relative paths, including numbered variants. Users
enter Fig/protein identities and fixed sample-slot counts, review thumbnails and
submit explicit batch assignments. Schema10 saves the entire source pool and the
confirmed mapping; adding sources or changing the plan invalidates confirmation.
Only a verified repeat of the same local path and content is skipped. Distinct
exports remain independent candidates even when their bytes match. Append imports
are saved after completion; failed confirmation saves remain unconfirmed.
This stage performs no automatic cropping or quantification. Independent grayscale
projects keep their existing OCR workflow. See
`../../docs/contracts/wb-instrument-intake-v1.md` for the current stage boundary.

T048's runtime builder now emits a separate Windows x64 test installer (minimum
Windows 10 1809), with mandatory desktop/Start menu/uninstall entries and app-local
MSVC redistributables from the locked Qt wheel. Its `win10-test` channel uses the
`Win10Test` settings namespace; T047's candidate and the original remain separate.
The native launcher keeps the existing candidate window label. An optional Start
menu environment check uses synthetic images and writes distinct local reports.
This is a test distribution, not a formal release or proof of clean Win10 acceptance.

T047 adds the approved project start screen and a local versioned navigation record.
New independent grayscale imports are saved and open the quantification page. Existing
projects restore valid page/row/Fig/lane selections. Recent entries are actual projects,
not demonstration links. A per-window session epoch rejects queued messages from a
retired host. Closing a project reuses the same web window with a fresh native host.
Scientific document schemas and completed measurements are unchanged.

The visible shell coordinates close, cancellation, save/discard and recovery. Unapplied
curve/lane drafts are distinct from unsaved project changes. Save failure keeps the
window visible and does not automatically retry the final save. Only the owned host
shuts down; other application instances are not terminated. The file menu and left
exit action use the same route as the native window close button.

The accepted T047 Windows candidate uses `python -m tooling.build_runtime_candidate
--iscc <verified compiler> --gcc <verified compiler>` from a clean checkout. It bundles
the same private CPython 3.12.14, locked production dependencies and four installed
product wheels. A native launcher uses the private interpreter with isolated imports,
forwards arguments/standard streams, waits for its exit and owns only its process tree.
The Inno installer has independent identity/directories/shortcuts and retains project
folders on uninstall. No external Python/uv is required. Build outputs, models and private
data are not committed. Unused Qt QML/development headers are excluded; the application
uses QtWidgets/WebEngineWidgets. The earlier `build_candidate.py` full-AOT experiment
did not pass installed startup/OCR validation and is not the delivered candidate.
`--verify-installation <new-report.json>` explicitly tests synthetic TIFF import, two-lane
durable worker results, offline OCR, save failure/reopen/cancellation and resource shutdown;
its report never replaces an
existing file. Passing this diagnostic does not establish scientific accuracy or clean
Windows/DPI acceptance. See the T047 task for actual build/validation status.

T045 extends the same workbench with WBQuant-style independent full-lane copying,
group reselection that retains completed runs, peak inclusion and bounded session
undo/redo. Fig-sheet detection runs in the existing background service, followed by
the normal durable measurement workers. Schema9 survives native view reconstruction;
its source-sheet group view does not require a newly composed montage. See
`../../docs/contracts/wb-fig-quant-v1.md` and the T045 task for actual validation.

The default `python -m bioimage_app` entry opens the current green WB web workbench.
For daily Windows use, `Start-BioImage.ps1` runs Python in isolated mode and verifies
the installed desktop module and shipped UI against its own checkout before dispatch.
A stale editable installation or missing UI stops with an actionable error; there is no
older-version fallback. `./Start-BioImage.ps1 --verify-launch` prints the verified paths
without opening Qt. Direct Python invocations do not receive this launcher protection.
`--web-workbench`, `--figure-project` and `--platform` all open that same workbench;
an unknown argument fails before Qt starts. Its hidden native host supplies asynchronous
storage, computation and advanced tools. Native editors open only on an explicit advanced
action; a failed close does not switch the interface to the hidden host.

The same workbench offers independent grayscale import: manual source-pixel targets,
explicit lane count/polarity, normal worker commits and saved results, without automatic
membrane detection or composition. A shipped local script presents free target selection
and all-lane/single-lane profiles; it never supplies quantitative results. See
`../../docs/contracts/wb-standalone-quant-v1.md` for identity/cancellation and compatibility.

Reviewed crops can be returned beside the locally selected original from the same workbench.
The project is saved first; the background rechecks the origin and publishes distinct verified
display PNG/raw TIFF files and a final receipt without replacement. Local origin paths never
enter project archives. See `../../docs/contracts/wb-crop-return-v1.md`.

Native compatibility windows require `--legacy-platform`, `--legacy-figure-project`, or
`--legacy-wb-manual` and have a title marked **兼容工具（旧版）**. `--wb-manual` remains a
historical alias for the last option. The old platform's static registry contains WB only;
its navigation/history contract remains for compatibility, with at most eight recent paths.
Worker routes remain unchanged and do not load the desktop window factory.

Version 0.14.0 adds schema7 laboratory segments and independent template file actions in
the existing template settings page. Template I/O runs in the tool background thread;
import saves the previous project, imports verified font bytes into the destination
workspace, then opens an empty project. Cancellation, close and generation checks reject
late replacements. Templates contain settings and fonts only; experiment row bindings,
measurements, OCR and normalization do not cross into the new project.

`bioimage_app.api` currently exposes AsyncStorage, StorageCommand and StorageReply.
The QObject worker owns Workspace/SQLite on its own QThread. Commands are an explicit
immutable FIFO, with request IDs, 64 pending-operation and 16 MiB document budgets.
Callbacks run on the owning GUI thread. Errors retain identity and do not stop the queue.
Keep the port alive until its asynchronous `closed` signal; shutdown drains accepted work.
Drained QObject workers retire on their own thread, move back to the owner, and stop
their former QThread. The owner checks thread exit without blocking, schedules deletion,
and publishes closure only after a queued destruction acknowledgement. The same lifecycle
applies to process decoding and project restore; this avoids a reproduced Qt object-lock/
Python GIL inversion during worker-thread QObject destruction.
The `bioimage_app.storage` DEBUG logger records only request identity, operation, phase,
monotonic time and native thread identity; it excludes paths, payloads and error text.
Pytest captures this logger for failed-test diagnosis. Logging does not change time limits
or establish the cause of an intermittent timeout; production DEBUG is disabled by default.
The caller must stop active processes before shutdown. Switching workspaces requires a
new port after closing the previous one. No database/Workspace objects are returned.

ProcessRunner owns one QProcess and a protocol decoder QThread. NDJSON frames are limited
to 4 MiB, the whole stdout stream to 8 MiB/8 frames, stderr to a 64 KiB tail. Only an
observed PID confirmed by storage unlocks the first request after hello. Cancellation
has a 5-second cooperative grace then stops the owned process tree. Windows uses a
KILL_ON_JOB_CLOSE Job Object attached before the request; registered workers wait before
spawning descendants. POSIX uses a fresh process session. Outcomes wait for process exit,
decoder shutdown and tree termination; they are not persisted success records.

RunSession connects the runner to AsyncStorage: PID registration, persisted cancellation,
observed exit receipt, then terminal CAS. Storage failures return an unsaved completion,
leaving recovery to the workspace instead of inventing terminal success. A thread-safe
cancellation Event is the one intentionally shared control signal; JSON remains immutable.
Keep session/port alive until completed/closed. Stop the session before closing storage.

The lazy `create_wb_codec` registration uses only wb_tool.api. Install `[wb]` for it.
Generic API import/wheel tests do not load WB/NumPy. No experimental formulas live here.
WBWindow explicitly assembles the optional WB page and background preview/document codec.
Run `uv run --locked --no-sync python -m bioimage_app` after installing `[wb]`.
The same static entry handles `--worker wb` without opening Qt; other modules are not
loaded from document strings. Manual import/ROI/band/baseline/run/save/reopen now works.
Close saves valid edits, cancels an active run, then drains and closes both threads.
Version 0.2.0 includes `--worker wb_ocr`, OCR-first drafts, separate composite assets,
explicit cell bindings, table review/export and v1/v2 document reopening. Original pixels
stay the measurement source. Automatic crop candidates, template composition, batch
normalization and packaging remain pending. Test with `uv run --locked --no-sync pytest
tests/test_async_storage.py tests/test_process_runner.py tests/test_run_session.py tests/test_wb_host.py`.

Version 0.3.0 adds the fixed-count grid drawing mode and asynchronous original-pixel TIFF
crop export. Margin exclusion is explicit; stored ROIs are not regenerated from defaults.
The crop includes source/coordinate provenance in ImageDescription and never replaces inputs.

Version 0.3.1 starts local DesktopDiagnostics only in the desktop entry (never in worker
routes). Each session gets a new log under logs in Qt's AppLocalDataLocation for
BioImageTools. Qt messages and uncaught Python errors are flushed with UTC/native thread IDs;
fatal Qt messages explicitly dump all Python thread stacks before Qt terminates. Normal
messages have a 1 MiB budget, individual messages 8192 characters; fatal stacks may exceed
it. No images or documents are serialized, and logs are not transmitted. Existing user
faulthandler configuration is preserved; its generic native fault output stays at its
configured destination. close() restores the prior Qt/Python hooks before closing the
owned descriptor. Logs are per-session and are not yet automatically rotated across runs.
The intermittent desktop Aborted root cause remains unknown; diagnostics are not a fix.

Version 0.4.0 adds create_figure_project_window / --figure-project and the multi-image project button in WBWindow. It assembles tool-owned review/template widgets, one asynchronous storage port and background rendering. New project drafts use tool_id wb-figure; old wb documents are unchanged. Batch TIFF imports deduplicate source SHA, edits revoke row review, save/close/reopen preserves asset identities, and template reuse saves the prior project before starting the next one. Export first persists the exact plan, then writes a new ZIP containing PNG/provenance/raw TIFF crops/originals. Preview may contain pending rows; export requires every row reviewed. Automatic candidates and project measurement/OCR integration are still pending.

Version 0.5.0 connects tool-owned crop candidates to the project window. Each background job freezes source SHA, row, revision and explicit N/height/polarity/settings. Per-source errors remain visible and do not stop subsequent rows. Cancellation retains earlier completed suggestions; generation changes discard the entire stale batch; close drains then saves retained suggestions before actual thread exit. Source decoding and candidate computation stay off the GUI thread. Project schema v1/v2 readers coexist; source/membrane focus is display-only and drawing still returns original coordinates. Project measurement/OCR integration remains pending.

Version 0.6.0 connects fixed-lane project annotations, sequential real WB processes, verified committed results, curve review and automatic project tables/XLSX. ProjectMeasurementSession freezes one saved project revision, verifies each prepared snapshot and uses existing RunSession PID/exit/commit arbitration. Completed run references are saved as a new draft; later edits reject batch attachment. Close cancels and drains the process before saving completed rows and shutting down threads. Reopen validates each run independently against Workspace.get_run via the new generic StorageCommand("run", run_id=...), then verifies result bytes and request identity in the tool background. A damaged/foreign run cannot suppress other valid rows. Source/ROI changes and parameter edits invalidate values; names do not withdraw geometry review. No platform fields/formulas or new dependency versions were added. Project OCR integration and final product acceptance remain pending.

Version 0.7.0 connects project OCR through ProjectOCRSession and the existing offline worker. Import a separate TIFF, review original text/confidence/positions, correct labels, explicitly bind each OCR row to a reviewed source row, then confirm to populate values. Recognition uses frozen v4 drafts and committed run assets; reopening revalidates both OCR and quantitative evidence. Failed/cancelled re-recognition preserves previous links. Late imports and process results cannot replace newer edits, and close waits for actual process/thread exit. Source review choices and OCR values refresh after edits. Both result panels share bounded pagination, and literal XLSX includes OCR and measurement provenance. Ordinary APIs remain lazy and platform semantics are unchanged. Unified archives and product acceptance remain pending.

Version 0.8.0 adds the tool-owned normalization panel with explicit target/reference rows, per-lane sample mappings and optional single/mean controls. Schema v5 preserves optional OCR plus all measurement references; no OCR is required for normalization. The background service rebuilds derived tables from verified results with generation checks. Automatic refresh and literal XLSX retain source/run identities, missing states and real zero values. Source geometry changes make mappings stale; edits withdraw confirmation. Formulas remain in wb_tool, with no experimental meaning added to platform_runtime. No dependency versions were changed except the local WB/desktop packages.

Version 0.9.0 connects PNG composite import and full-size generation directly to project OCR. A saved revision is rendered/encoded off the GUI thread with embedded source provenance, then imported as immutable bytes before the existing OCR session runs. Generic StorageCommand("import_bytes") validates the digest and uses an owned temporary file in the storage thread; its payload budget is 64 MiB, while documents/read operations retain 16 MiB. The runtime has no new experimental fields. Save completion preserves later edits, generated/imported sources reject cancelled or stale callbacks, and one coalesced derived-table timer preserves operation errors. The single-image composite selector also accepts PNG; quantitative TIFF imports are unchanged.

Version 0.10.0 assembles the tool-owned batch metadata page. XLSX/CSV reads run off the GUI thread; cancellation, close and newer edits reject late results without replacing the previous book. Source imports produce bounded thumbnails, continue after decoding errors and deduplicate by SHA. Reopened projects can explicitly load thumbnails in a sequential cancellable batch. Metadata preview/application keeps original assets and completed runs; the existing project validity rules suppress stale derived values. No platform storage schema or numerical formula changes.

Version 0.11.0 adds CSV choices and unified project ZIP results. After saving the exact revision, ProjectArchiveSession resolves each recorded run and asset through AsyncStorage; tool background re-reads verified request/result bytes before deriving any exported values. Bad evidence is isolated per run and recorded explicitly. Export cancellation/close/generation changes prevent pending publication, while prior files stay immutable. Source/measurement/OCR/normalization CSV and XLSX share the same result builders. Archive v2 includes per-member checksums and original run evidence; portable ZIP import remains a separate task. No platform schema or numerical formula changes.

Version 0.12.0 adds ZIP restore into a new workspace. A dedicated thread validates the archive, imports immutable assets and a single retained revision, closes SQLite, then publishes without replacing an existing destination. Completion waits for actual thread exit. Imported history is never registered as local runs; reopen revalidates copied evidence independently, edits invalidate prior values, and recomputation uses real RunSession receipts. Close/cancel and failed publication retain explicit outcomes. platform-runtime0.2.0 adds only generic initial snapshot import and an incomplete-publication guard.

Version 0.13.0 adds a separate direct TIFF/PNG figure button. It saves the exact project revision before background rendering and publication; cancel, close or a later edit prevents pending output, including during the save callback. Already published images remain available. The tool validates complete pixels, provenance and DPI after writing. Display TIFFs enter the existing OCR workflow with explicit source-row binding, while quantitative import rejects known display outputs. Full portable projects still use ZIP; no platform or numerical schema changes.

T-024 default launch now opens the tool platform with the real WB entry and recent workspaces. Directory import runs tool-owned lane/crop/bound suggestions, committed measurement processes and atomic result-directory export. Reopen verifies evidence and selects a source. Cancellation, errors and stale rows remain explicit. See `../../docs/contracts/wb-automatic-v1.md` and the T-024 task for validation and limitations.

T-034 adds explicit `--web-workbench`: the package's local `web_ui/index.html` is rendered
unchanged in a Qt WebEngine shell. Its WebChannel `workbench.request(action, JSON)` adapter
routes native file selection and existing WB operations; `stateChanged(JSON)` carries
read-only display rasters, original-pixel crop geometry and real result states. `refresh`
requests an initial snapshot. Crop requires selected row ID plus source SHA; stale, busy,
out-of-bounds and non-integer commands are rejected. Original pixels remain solely in the
existing WB pipeline. Metadata, OCR, normalization and templates open the native advanced
window explicitly; these are not claimed to be web-ported. Closing that window hides it;
closing the shell cancels/drains/saves through the existing host lifecycle. The local page
rejects foreign navigation and requests outside its asset root (except image data URLs and
Qt's WebChannel resource). Each shell uses an off-the-record profile. Existing default
platform/native routes remain available. This is a developer entry, not a packaged release.


T067执行计划页可明确进入采集组修改；编辑中禁止继续处理，保存并确认后按失效范围继续。原Storage/CAS和历史结果保留，见 ../../docs/contracts/wb-intake-group-revision-v1.md。
