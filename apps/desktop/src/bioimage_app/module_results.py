"""Storage-thread admission of module files before the existing terminal transaction."""

import stat
from pathlib import Path
from threading import Event

from platform_runtime.api import StateConflict, Workspace, WorkspaceError
from tool_contracts.api import (
    BoundAsset,
    ExecutionRequest,
    OutputManifest,
    ProcessExitReceipt,
    RunRecord,
    canonical_module_json,
)

MAX_MODULE_OUTPUT_BYTES = 16 * 1024 * 1024


def _plain(path: Path) -> None:
    for item in (path, *path.parents):
        info = item.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("Module output cannot use links or reparse points")
        if item == path and stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
            raise ValueError("Module output cannot be a hard link")


def commit_module_result(
    store: Workspace,
    run_id: str,
    receipt: ProcessExitReceipt,
    data: bytes,
    request: ExecutionRequest,
    output_directory: str,
    cancellation: Event | None,
) -> RunRecord:
    """Only called after OS exit. Imported-but-uncommitted assets are retained on failure."""
    run = store.get_run(run_id)
    if (
        run.state != "running"
        or run.pid != receipt.pid
        or receipt.run_id != run_id
        or receipt.exit_code != 0
        or receipt.pid == 0
    ):
        raise StateConflict("Module publication requires the owned successful process exit")

    def check_cancel() -> None:
        if cancellation is not None and cancellation.is_set():
            store.request_cancel(run_id)
            raise StateConflict("Module publication cancelled before commit")

    check_cancel()
    try:
        request = ExecutionRequest.model_validate_json(request.model_dump_json())
        frozen = ExecutionRequest.model_validate_json(store.read_asset(run.request))
        if frozen != request or (run.document_id, run.revision) != (
            request.document_id,
            request.revision,
        ):
            raise ValueError("Persisted run request differs from the frozen module request")
        manifest = OutputManifest.model_validate_json(canonical_module_json(data.decode("utf-8")))
        if (
            manifest.publication != "candidate"
            or manifest.request != request
            or manifest.run_id != run_id
        ):
            raise ValueError("Candidate manifest does not belong to this run")
        for source in request.inputs:
            store.asset_path(source.asset)
        directory = Path(output_directory)
        if not directory.is_absolute():
            raise ValueError("Module output directory must be host-owned and absolute")
        _plain(directory)
        if not directory.is_dir() or {p.name for p in directory.iterdir()} != {
            port.filename for port in request.module.output_ports
        }:
            raise ValueError("Module output set is missing or contains undeclared files")
        if sum(output.asset.size_bytes for output in manifest.outputs) > MAX_MODULE_OUTPUT_BYTES:
            raise ValueError("Module output exceeds the 16MiB admission budget")
        # Validate all paths and sizes before importing the first file.
        for output in manifest.outputs:
            path = directory / output.asset.relative_path
            _plain(path)
            if not path.is_file() or path.stat().st_size != output.asset.size_bytes:
                raise ValueError("Module output size differs from its candidate manifest")
        imported: list[BoundAsset] = []
        for output in manifest.outputs:
            check_cancel()
            ref = store.import_asset(directory / output.asset.relative_path, output.asset.sha256)
            if ref.size_bytes != output.asset.size_bytes:
                raise ValueError("Module output changed during import")
            imported.append(BoundAsset(port=output.port, kind=output.kind, asset=ref))
        committed = OutputManifest(
            run_id=run_id,
            request=request,
            publication="committed",
            outputs=tuple(imported),
            quality=manifest.quality,
            summary_json=manifest.summary_json,
        )
    except StateConflict:
        raise
    except (ValueError, OSError, WorkspaceError) as exc:
        check_cancel()
        return store.finish_failure(
            run_id, receipt, reason="module_output_invalid:" + str(exc)[:1024]
        )
    check_cancel()
    return store.commit_result(
        run_id,
        receipt,
        committed.model_dump_json().encode("utf-8"),
        cancelled=cancellation.is_set if cancellation is not None else None,
    )
