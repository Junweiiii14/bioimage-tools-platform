"""One-shot shared comparison controller for CLI and the existing web workbench."""

import json
import sys
from pathlib import Path
from threading import Event
from uuid import uuid4

from PySide6.QtCore import QObject, Signal, Slot
from tool_contracts.api import (
    AssetRef,
    ExecutionRequest,
    OutputManifest,
    ProcessExitReceipt,
    RunRecord,
)
from wb_tool.api import (
    WBJob,
    WBModuleInput,
    WBModuleStart,
    WBReply,
    create_wb_background,
    encode_module_frame,
    module_identity,
)

from bioimage_app.run_session import RunCompletion, RunSession
from bioimage_app.storage import AsyncStorage, StorageCommand, StorageReply
from bioimage_app.wb_registration import WBModuleProcessCodec


class ComparisonSession(QObject):
    """Keep alive until finished: it means both background services actually closed."""

    changed = Signal(str)
    finished = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._store = AsyncStorage(self)
        self._background = create_wb_background()
        self._background.setParent(self)
        self._store.replied.connect(self._storage_reply)
        self._background.replied.connect(self._background_reply)
        self._store.closed.connect(self._store_closed)
        self._background.closed.connect(self._background_closed)
        self._storage_pending: dict[str, str] = {}
        self._background_pending: dict[str, str] = {}
        self._run_session: RunSession | None = None
        self._run_done = False
        self._cancel = Event()
        self._closing = False
        self._closed_services = 0
        self._used = False
        self._input: WBModuleInput | None = None
        self._asset: AssetRef | None = None
        self._request: ExecutionRequest | None = None
        self._run: RunRecord | None = None
        self._manifest: OutputManifest | None = None
        self._remaining: list[AssetRef] = []
        self._sources_to_verify: list[AssetRef] = []
        self._read_port = ""
        self.workspace = ""
        self.state = "idle"
        self.message = ""
        self._files: dict[str, str] = {}
        self._tables: dict[str, str] = {}

    def snapshot(self) -> str:
        return json.dumps(
            {
                "state": self.state,
                "message": self.message,
                "workspace": self.workspace,
                "run": self._run.model_dump(mode="json") if self._run else None,
                "quality": self._manifest.quality if self._manifest else None,
                "summary_json": self._manifest.summary_json if self._manifest else "{}",
                "files": self._files,
                "tables_json": self._tables,
            },
            ensure_ascii=False,
        )

    def _publish(self, state: str, message: str) -> None:
        self.state, self.message = state, message
        self.changed.emit(self.snapshot())

    def _claim(self, workspace: str) -> None:
        if self._used:
            raise RuntimeError("对照会话只能使用一次")
        self._used = True
        self.workspace = str(Path(workspace).absolute())
        self._publish("preparing", "正在准备冻结输入")

    def start_fixture(self, workspace: str, name: str = "triangle_u16") -> None:
        self._claim(workspace)
        self._job("input", WBJob("module_fixture", row_id=name, cancellation=self._cancel))

    def start_input(self, workspace: str, source: str, parameters: str) -> None:
        self._claim(workspace)
        self._job(
            "input",
            WBJob("module_input", path=source, destination=parameters, cancellation=self._cancel),
        )

    def reopen(self, workspace: str) -> None:
        self._claim(workspace)
        self._publish("opening", "正在核验已保存工程")
        self._submit("opened", StorageCommand("open", path=self.workspace))

    def cancel(self) -> None:
        if self._closing or self._run_done:
            return
        self._cancel.set()
        self._publish("cancelling", "正在取消并等待退出")
        if self._run_session is not None:
            self._run_session.cancel()

    def _submit(self, purpose: str, command: StorageCommand) -> None:
        self._storage_pending[self._store.submit(command)] = purpose

    def _job(self, purpose: str, job: WBJob) -> None:
        self._background_pending[self._background.submit(job)] = purpose

    def _failure(self, reason: str) -> None:
        self._files.clear()
        self._tables.clear()
        self._publish("failed", reason)
        self._shutdown()

    def _before_run_cancel(self) -> bool:
        if not self._cancel.is_set() or self._run_session is not None or self._run_done:
            return False
        if self._run is not None and self._run.state == "prepared":
            self._submit("cancel_before_start", StorageCommand("cancel", run_id=self._run.run_id))
        else:
            self._publish("cancelled", "已取消；未提交新结果")
            self._shutdown()
        return True

    @Slot(object)
    def _background_reply(self, reply: WBReply) -> None:
        purpose = self._background_pending.pop(reply.request_id, None)
        if purpose is None or self._closing:
            return
        try:
            if self._before_run_cancel():
                return
            if reply.error:
                self._failure(reply.error)
            elif purpose == "input" and isinstance(reply.value, WBModuleInput):
                self._input = reply.value
                self._submit("created", StorageCommand("create", path=self.workspace))
            elif purpose == "request" and isinstance(reply.value, ExecutionRequest):
                self._request = reply.value
                self._submit(
                    "saved",
                    StorageCommand(
                        "save",
                        document_id=reply.value.document_id,
                        tool_id="wb-v0-compare",
                        revision=reply.value.revision,
                        data=reply.value.model_dump_json().encode("utf-8"),
                    ),
                )
            elif purpose == "manifest" and isinstance(reply.value, OutputManifest):
                manifest = reply.value
                run = self._run
                if (
                    run is None
                    or manifest.publication != "committed"
                    or manifest.run_id != run.run_id
                    or (manifest.request.document_id, manifest.request.revision)
                    != (run.document_id, run.revision)
                ):
                    raise ValueError("保存的成果与运行身份不一致")
                self._manifest = manifest
                self._submit("frozen_request", StorageCommand("read", asset=run.request))
            elif purpose.startswith("table:") and isinstance(reply.value, str):
                self._tables[purpose.removeprefix("table:")] = reply.value
                self._read_next()
            else:
                raise ValueError("后台返回了不匹配的对照数据")
        except (ValueError, OSError, RuntimeError) as exc:
            self._failure(str(exc))

    @Slot(object)
    def _storage_reply(self, reply: StorageReply) -> None:
        purpose = self._storage_pending.pop(reply.request_id, None)
        if purpose is None or self._closing:
            return
        try:
            if reply.error_code:
                self._failure(reply.message or reply.error_code)
                return
            if purpose == "prepared" and isinstance(reply.value, RunRecord):
                self._run = reply.value
            if (
                purpose not in ("cancel_before_start", "cancelled_before_start")
                and self._before_run_cancel()
            ):
                return
            self._storage_step(purpose, reply)
        except (ValueError, OSError, RuntimeError) as exc:
            self._failure(str(exc))

    def _storage_step(self, purpose: str, reply: StorageReply) -> None:
        if purpose == "created":
            supplied = self._input
            if supplied is None:
                raise ValueError("缺少冻结输入")
            self._submit(
                "imported",
                StorageCommand(
                    "import_bytes" if supplied.source_bytes else "import",
                    path="fixture.tif" if supplied.source_bytes else supplied.source_path,
                    data=supplied.source_bytes,
                    source_sha256=supplied.request.source_sha256,
                ),
            )
        elif purpose == "imported" and isinstance(reply.value, AssetRef):
            self._asset = reply.value
            if self._input is None:
                raise ValueError("缺少冻结参数")
            self._job(
                "request",
                WBJob(
                    "module_prepare",
                    module_asset=reply.value,
                    module_parameters=self._input.request,
                    row_id="compare-" + uuid4().hex,
                    cancellation=self._cancel,
                ),
            )
        elif purpose == "saved" and self._request is not None:
            self._submit(
                "prepared", StorageCommand("prepare", document_id=self._request.document_id)
            )
        elif purpose == "prepared" and self._asset is not None:
            self._submit("source_path", StorageCommand("asset", asset=self._asset))
        elif purpose == "source_path" and isinstance(reply.value, str):
            self._launch(reply.value)
        elif purpose == "opened":
            self._submit("runs", StorageCommand("runs"))
        elif purpose == "runs" and isinstance(reply.value, tuple):
            runs = [
                run
                for run in reply.value
                if isinstance(run, RunRecord) and run.tool_id == "wb-v0-compare"
            ]
            if not runs:
                raise ValueError("工程没有旧方法对照运行；原WB项目请从原项目入口打开")
            self._run = runs[0]
            self._run_done = True
            self._load_result()
        elif purpose == "manifest":
            self._job("manifest", WBJob("module_manifest", data=reply.data))
        elif purpose == "frozen_request" and self._manifest is not None:
            if reply.data != self._manifest.request.model_dump_json().encode("utf-8"):
                raise ValueError("成果请求与持久化冻结请求不一致")
            self._remaining = [output.asset for output in self._manifest.outputs]
            self._sources_to_verify = [item.asset for item in self._manifest.request.inputs]
            self._verify_source()
        elif purpose == "source_verified":
            self._verify_source()
        elif purpose == "output" and self._manifest is not None:
            output = next(item for item in self._manifest.outputs if item.port == self._read_port)
            self._files[output.port] = str(Path(self.workspace) / output.asset.relative_path)
            if output.port in ("measurements", "differences"):
                self._job("table:" + output.port, WBJob("module_table", data=reply.data))
            else:
                self._read_next()
        elif purpose == "cancel_before_start" and isinstance(reply.value, RunRecord):
            self._submit(
                "cancelled_before_start",
                StorageCommand(
                    "cancelled",
                    run_id=reply.value.run_id,
                    receipt=ProcessExitReceipt(run_id=reply.value.run_id, pid=0, exit_code=None),
                ),
            )
        elif purpose == "cancelled_before_start" and isinstance(reply.value, RunRecord):
            self._run = reply.value
            self._publish("cancelled", "已取消；未启动计算")
            self._shutdown()
        else:
            raise ValueError("存储返回了不匹配的对照数据")

    def _launch(self, source: str) -> None:
        if self._request is None or self._run is None:
            raise ValueError("运行缺少冻结请求")
        output = str(Path(self.workspace) / "v0-compare")
        start = WBModuleStart(
            identity=module_identity(self._run.run_id, self._request),
            request=self._request,
            source_path=source,
            output_directory=output,
        )
        self._run_session = RunSession(
            self._store,
            self._run,
            WBModuleProcessCodec(start),
            self,
            module_request=self._request,
            module_output_directory=output,
        )
        self._run_session.completed.connect(self._completed)
        command = (
            (sys.executable, "--worker", "wb_v0_compare")
            if getattr(sys, "frozen", False)
            else (sys.executable, "-I", "-m", "bioimage_app", "--worker", "wb_v0_compare")
        )
        self._publish("running", "正在执行旧方法和独立模块对照")
        self._run_session.start(command, self.workspace, encode_module_frame(start))

    @Slot(object)
    def _completed(self, completion: RunCompletion) -> None:
        self._run_done = True
        self._run = completion.record
        if completion.error or self._run is None:
            self._failure(completion.error or "运行终态未保存")
        else:
            self._load_result()

    def _load_result(self) -> None:
        run = self._run
        if run is None:
            raise ValueError("没有持久化运行")
        if run.state == "succeeded" and run.result is not None:
            self._publish("verifying", "正在重读并核验已提交成果")
            self._submit("manifest", StorageCommand("read", asset=run.result))
        else:
            self._publish(run.state, run.reason or "运行已取消；没有成功结果")
            self._shutdown()

    def _read_next(self) -> None:
        if self._manifest is None:
            raise ValueError("缺少已提交成果")
        if self._remaining:
            asset = self._remaining.pop(0)
            self._read_port = next(
                item.port for item in self._manifest.outputs if item.asset == asset
            )
            self._submit("output", StorageCommand("read", asset=asset))
        else:
            self._publish(
                "succeeded",
                "成果已保存并核验"
                if self._manifest.quality == "complete"
                else "对照已保存；包含异常或待复核测量",
            )
            self._shutdown()

    def _verify_source(self) -> None:
        if self._sources_to_verify:
            self._submit(
                "source_verified", StorageCommand("asset", asset=self._sources_to_verify.pop(0))
            )
        else:
            self._read_next()

    def _shutdown(self) -> None:
        if not self._closing:
            self._closing = True
            self._store.shutdown()
            self._background.shutdown()

    @Slot()
    def _store_closed(self) -> None:
        self._service_closed()

    @Slot()
    def _background_closed(self) -> None:
        self._service_closed()

    def _service_closed(self) -> None:
        self._closed_services += 1
        if self._closed_services == 2:
            self.finished.emit(self.snapshot())
