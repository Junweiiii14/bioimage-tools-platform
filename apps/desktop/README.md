# Desktop host

`bioimage_app.api` currently exposes AsyncStorage, StorageCommand and StorageReply.
The QObject worker owns Workspace/SQLite on its own QThread. Commands are an explicit
immutable FIFO, with request IDs, 64 pending-operation and 16 MiB document budgets.
Callbacks run on the owning GUI thread. Errors retain identity and do not stop the queue.
Keep the port alive until its asynchronous `closed` signal; shutdown drains accepted work.
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
