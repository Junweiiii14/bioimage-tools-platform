# Desktop host

`bioimage_app.api` currently exposes AsyncStorage, StorageCommand and StorageReply.
The QObject worker owns Workspace/SQLite on its own QThread. Commands are an explicit
immutable FIFO, with request IDs, 64 pending-operation and 16 MiB document budgets.
Callbacks run on the owning GUI thread. Errors retain identity and do not stop the queue.
Keep the port alive until its asynchronous `closed` signal; shutdown drains accepted work.
The caller must stop active processes before shutdown. Switching workspaces requires a
new port after closing the previous one. No database/Workspace objects are returned.

QProcess lifecycle, WB UI and executable entry are still under implementation (T-007).
No experimental formulas live here. Test with `uv run --locked --no-sync pytest tests/test_async_storage.py`.
