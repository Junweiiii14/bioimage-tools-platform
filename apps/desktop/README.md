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
WB UI and executable entry are still pending. Test with `uv run --locked --no-sync pytest
tests/test_async_storage.py tests/test_process_runner.py tests/test_run_session.py tests/test_wb_host.py`.
