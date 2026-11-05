"""Input, identity, candidate safety and zero/failure boundaries without model downloads."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import tifffile
from nuclei_tool.adapters import execute as execution
from nuclei_tool.adapters.inference import NucleiCancelled
from nuclei_tool.adapters.input import read_nuclei_input
from nuclei_tool.adapters.protocol import (
    NucleiCancel,
    NucleiConversation,
    NucleiStart,
    encode_frame,
    execution_identity,
)
from nuclei_tool.adapters.registration import nuclei_module_spec, research_environment, verify_model
from nuclei_tool.application.contracts import NucleiParameters
from nuclei_tool.domain.labels import validate_labels
from numpy.typing import NDArray
from PIL import Image, TiffImagePlugin
from tool_contracts.api import (
    AssetRef,
    BoundAsset,
    ExecutionEvent,
    ExecutionRequest,
    canonical_module_json,
)


def start_for(source: Path, output: Path, model: Path) -> NucleiStart:
    supplied = read_nuclei_input(str(source))
    raw = canonical_module_json(
        NucleiParameters(
            source_sha256=supplied.sha256,
            shape_yx=supplied.pixels.shape,
        ).model_dump_json()
    )
    request = ExecutionRequest(
        request_id="request",
        execution_id="execution",
        node_id="segment",
        attempt_id="attempt",
        document_id="document",
        revision=0,
        module=nuclei_module_spec(),
        inputs=(
            BoundAsset(
                port="source",
                kind="raw_image",
                asset=AssetRef(
                    asset_id="source",
                    relative_path="source.tif",
                    sha256=supplied.sha256,
                    size_bytes=supplied.size_bytes,
                ),
            ),
        ),
        parameters_json=raw,
        parameters_sha256=hashlib.sha256(raw.encode()).hexdigest(),
        environment=research_environment(),
    )
    return NucleiStart(
        identity=execution_identity("run", request),
        request=request,
        source_path=str(source),
        output_directory=str(output),
        model_directory=str(model),
    )


@pytest.fixture
def start(tmp_path: Path) -> NucleiStart:
    source = tmp_path / "source.tif"
    Image.fromarray(np.arange(48, dtype=np.uint8).reshape(6, 8)).save(source)
    return start_for(source, tmp_path / "outputs", tmp_path / "model")


@pytest.mark.parametrize("kind", ("rgb", "uint16", "float", "pages", "orientation", "white"))
def test_reject_unsupported_input(tmp_path: Path, kind: str) -> None:
    path = tmp_path / "bad.tif"
    tags = TiffImagePlugin.ImageFileDirectory_v2()
    if kind == "rgb":
        image = Image.fromarray(np.zeros((8, 9, 3), dtype=np.uint8))
    elif kind == "uint16":
        image = Image.fromarray(np.zeros((8, 9), dtype=np.uint16))
    elif kind == "float":
        image = Image.fromarray(np.zeros((8, 9), dtype=np.float32))
    else:
        image = Image.fromarray(np.zeros((8, 9), dtype=np.uint8))
    if kind == "orientation":
        tags[274] = 6
    if kind == "white":
        tags[262] = 0
    image.save(
        path,
        tiffinfo=tags,
        save_all=kind == "pages",
        append_images=[image] if kind == "pages" else [],
    )
    with pytest.raises(ValueError, match="unsupported_input"):
        read_nuclei_input(str(path))


def test_pixels_original_and_readonly(start: NucleiStart) -> None:
    supplied = read_nuclei_input(start.source_path)
    np.testing.assert_array_equal(supplied.pixels, np.arange(48).reshape(6, 8))
    assert not supplied.pixels.flags.writeable


def test_signed_tiff_is_rejected_before_reinterpreting_negative_pixels(tmp_path: Path) -> None:
    path = tmp_path / "signed.tif"
    tifffile.imwrite(path, np.array([[-1, 0, 1], [127, -128, 3]], dtype=np.int8))
    original = path.read_bytes()
    with pytest.raises(ValueError, match="unsupported_input"):
        read_nuclei_input(str(path))
    assert path.read_bytes() == original


def test_invalid_labels_not_zero() -> None:
    for labels in (
        np.zeros((3, 4), dtype=float),
        np.full((3, 4), -1),
        np.full((3, 4), 2**32, dtype=np.uint64),
    ):
        with pytest.raises(ValueError, match="invalid_labels"):
            validate_labels(labels, (3, 4))
    labels = np.zeros((3, 4), dtype=np.uint32)
    labels[1, 2], labels[2, 3] = 4, 19
    assert validate_labels(labels, (3, 4))[1] == 2


def test_zero_is_valid_and_preserves_input(
    start: NucleiStart, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = Path(start.source_path).read_bytes()

    def zero(*_args: object) -> NDArray[np.uint32]:
        return np.zeros((6, 8), dtype=np.uint32)

    monkeypatch.setattr(execution, "predict", zero)
    manifest = execution.execute(start, lambda: False)
    assert json.loads(manifest.summary_json)["nuclei_count"] == 0
    assert manifest.publication == "candidate"
    assert Path(start.source_path).read_bytes() == original
    with pytest.raises(ValueError, match="output_exists"):
        execution.execute(start, lambda: False)


def test_failure_and_cancel_have_no_candidate(
    start: NucleiStart, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(*_args: object) -> NDArray[np.uint32]:
        raise RuntimeError("model failure")

    monkeypatch.setattr(execution, "predict", fail)
    with pytest.raises(RuntimeError, match="model failure"):
        execution.execute(start, lambda: False)
    assert not Path(start.output_directory).exists()
    with pytest.raises(NucleiCancelled):
        execution.execute(start, lambda: True)
    assert not Path(start.output_directory).exists()


def test_cancel_after_predict_has_no_candidate(
    start: NucleiStart, monkeypatch: pytest.MonkeyPatch
) -> None:
    stopped = False

    def predicted(*_args: object) -> NDArray[np.uint32]:
        nonlocal stopped
        stopped = True
        return np.zeros((6, 8), dtype=np.uint32)

    monkeypatch.setattr(execution, "predict", predicted)
    with pytest.raises(NucleiCancelled):
        execution.execute(start, lambda: stopped)
    assert not Path(start.output_directory).exists()


def test_input_hash_and_module_mismatch(start: NucleiStart) -> None:
    Path(start.source_path).write_bytes(Path(start.source_path).read_bytes() + b"changed")
    with pytest.raises(ValueError, match="input_mismatch"):
        execution.execute(start, lambda: False)
    changed = start.request.module.model_copy(update={"implementation_digest": "0" * 64})
    request = start.request.model_copy(update={"module": changed})
    with pytest.raises(ValueError, match="implementation_mismatch"):
        execution.execute(start.model_copy(update={"request": request}), lambda: False)


def test_missing_and_wrong_model(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="model_missing"):
        verify_model(str(tmp_path / "missing"))
    (tmp_path / "config.json").write_text("{}")
    with pytest.raises(ValueError, match="model_digest_mismatch"):
        verify_model(str(tmp_path))


def test_protocol_identity_sequence(start: NucleiStart) -> None:
    codec = NucleiConversation(start)
    codec.accept(encode_frame(ExecutionEvent(kind="hello", sequence=0)))
    with pytest.raises(ValueError):
        codec.accept(encode_frame(ExecutionEvent(kind="hello", sequence=0)))
    codec.accept(encode_frame(ExecutionEvent(kind="accepted", sequence=1, identity=start.identity)))
    control = NucleiCancel.model_validate_json(codec.cancellation())
    assert control.identity == start.identity
    with pytest.raises(ValueError):
        codec.cancellation()
    wrong = start.identity.model_copy(update={"run_id": "wrong"})
    with pytest.raises(ValueError, match="another attempt"):
        codec.accept(encode_frame(ExecutionEvent(kind="cancelled", sequence=2, identity=wrong)))


def test_worker_lightweight_hello_and_failure(start: NucleiStart) -> None:
    # Desktop intentionally lacks research dependencies: actual process must fail,
    # not import the model before hello or publish a fabricated empty result.
    result = subprocess.run(
        [sys.executable, "-I", "-m", "nuclei_tool.worker"],
        input=encode_frame(start),
        capture_output=True,
        timeout=20,
        check=False,
    )
    events = [ExecutionEvent.model_validate_json(line) for line in result.stdout.splitlines()]
    assert [event.kind for event in events] == ["hello", "accepted", "failure"]
    assert result.returncode == 2
    assert not Path(start.output_directory).exists()


def test_open_control_pipe_does_not_block_native_import() -> None:
    # Regression for a real Windows deadlock: blocking CRT read in a listener
    # while NumPy's native DLL loads. Keep stdin open, unlike communicate(input=).
    code = """
import sys
from threading import Thread
from nuclei_tool.worker import LineReader
reader = LineReader(sys.stdin.fileno())
thread = Thread(target=reader.read, daemon=True)
thread.start()
import numpy
reader.stopped.set()
thread.join(timeout=1)
assert not thread.is_alive()
print('native_import_complete')
"""
    process = subprocess.Popen(
        [sys.executable, "-I", "-c", code],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        process.wait(timeout=15)
    finally:
        if process.poll() is None:
            process.kill()
        output, errors = process.communicate(timeout=5)
    assert process.returncode == 0, errors.decode(errors="replace")
    assert b"native_import_complete" in output


def test_long_model_error_still_emits_terminal_failure(start: NucleiStart) -> None:
    code = """
import nuclei_tool.adapters.execute as execution
from nuclei_tool.worker import main
def fail(*args):
    raise RuntimeError('x' * 1200)
execution.execute = fail
raise SystemExit(main())
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code],
        input=encode_frame(start),
        capture_output=True,
        timeout=20,
        check=False,
    )
    events = [ExecutionEvent.model_validate_json(line) for line in result.stdout.splitlines()]
    assert result.returncode == 2
    assert [event.kind for event in events] == ["hello", "accepted", "failure"]
    assert len(events[-1].reason) == 1024
    assert events[-1].reason.startswith("RuntimeError: ")
    assert not Path(start.output_directory).exists()
