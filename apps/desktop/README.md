# Desktop host

The default `python -m bioimage_app` entry opens the current green WB web workbench.
`--web-workbench`, `--figure-project` and `--platform` all open that same workbench;
an unknown argument fails before Qt starts. Its hidden native host supplies asynchronous
storage, computation and advanced tools. Native editors open only on an explicit advanced
action; a failed close does not switch the interface to the hidden host.

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
