"""Real worker execution and adversarial wire messages through the public API."""

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import cast

import numpy as np
import pytest
import tifffile
from pydantic import JsonValue, ValidationError
from wb_tool.api import (
    AcceptedFrame,
    AnalysisRequest,
    BandAnnotation,
    BandBounds,
    CancelFrame,
    CancelledFrame,
    FailureFrame,
    HelloFrame,
    LaneAnnotation,
    LaneROI,
    ProtocolErrorFrame,
    ResultFrame,
    StartFrame,
    WorkerConversation,
    analyze_annotations,
    encode_worker_frame,
    load_tiff,
    parse_worker_frame,
    worker_protocol_schema,
)


@pytest.fixture
def start(tmp_path: Path) -> StartFrame:
    path = tmp_path / "中文分析输入.tif"
    tifffile.imwrite(path, np.array([[245], [235], [245]], dtype=np.uint8))
    image = load_tiff(path)
    request = AnalysisRequest(
        image.sha256,
        7,
        "dark",
        (LaneAnnotation(LaneROI("L", 0, 0, 1, 3), (BandAnnotation("B", BandBounds(0, 2)),)),),
    )
    return StartFrame(
        protocol_version=1,
        kind="start",
        sequence=0,
        run_id="run-1",
        attempt_id="attempt-1",
        request_id="request-1",
        source_path=str(path),
        request=request,
    )


def result_frame(start: StartFrame) -> ResultFrame:
    result = analyze_annotations(load_tiff(start.source_path), start.request)
    return ResultFrame(
        protocol_version=1,
        kind="result",
        sequence=2,
        run_id=start.run_id,
        attempt_id=start.attempt_id,
        request_id=start.request_id,
        result=result,
    )


def change(data: dict[str, JsonValue], path: tuple[str | int, ...], value: JsonValue) -> None:
    current: JsonValue = data
    for key in path[:-1]:
        if isinstance(key, str):
            assert isinstance(current, dict)
            current = current[key]
        else:
            assert isinstance(current, list)
            current = cast(list[JsonValue], current)[key]
    key = path[-1]
    if isinstance(key, str):
        assert isinstance(current, dict)
        current[key] = value
    else:
        assert isinstance(current, list)
        current[key] = value


def test_strict_round_trip_and_schema(start: StartFrame) -> None:
    assert parse_worker_frame(encode_worker_frame(start)) == start
    result = result_frame(start)
    assert parse_worker_frame(encode_worker_frame(result)) == result
    schema = worker_protocol_schema()
    saved = Path(__file__).resolve().parents[3] / "docs/contracts/wb-worker-v1.schema.json"
    assert json.loads(saved.read_text(encoding="utf-8")) == schema


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("extra",), 1),
        (("protocol_version",), True),
        (("protocol_version",), 2),
        (("sequence",), False),
        (("request", "revision"), "7"),
        (("request", "revision"), True),
        (("request", "extra"), 1),
        (("request", "lanes", 0, "roi", "extra"), 1),
        (("request", "lanes", 0, "roi", "x0"), False),
        (("request", "lanes", 0, "bands", 0, "bounds", "right"), 0),
    ],
)
def test_invalid_requests_rejected(
    start: StartFrame, path: tuple[str | int, ...], value: JsonValue
) -> None:
    data = cast(dict[str, JsonValue], json.loads(start.model_dump_json()))
    change(data, path, value)
    with pytest.raises((ValueError, ValidationError)):
        parse_worker_frame(json.dumps(data).encode())


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("result", "bit_depth"), 32),
        (("result", "schema_version"), True),
        (("result", "lanes", 0, "roi", "lane_id"), "wrong-lane"),
        (("result", "lanes", 0, "profiles", "quantitative", 1), 300),
        (("result", "lanes", 0, "profiles", "raw", 1), float("nan")),
        (("result", "lanes", 0, "bands", 0, "measurement", "signal"), float("inf")),
        (("result", "lanes", 0, "bands", 0, "measurement", "signal"), -1),
        (("result", "lanes", 0, "bands", 0, "measurement", "baseline", "left_value"), 0),
        (("result", "lanes", 0, "bands", 0, "status"), "quality_review"),
        (("result", "lanes", 0, "bands", 0, "quality_flags"), ["dtype_min_present"]),
    ],
)
def test_inconsistent_results_rejected(
    start: StartFrame, path: tuple[str | int, ...], value: JsonValue
) -> None:
    data = cast(dict[str, JsonValue], json.loads(result_frame(start).model_dump_json()))
    change(data, path, value)
    with pytest.raises((ValueError, ValidationError)):
        parse_worker_frame(json.dumps(data).encode())


def conversation(start: StartFrame) -> WorkerConversation:
    session = WorkerConversation(start)
    session.accept(encode_worker_frame(HelloFrame(protocol_version=1, kind="hello", sequence=0)))
    session.accept(
        encode_worker_frame(
            AcceptedFrame(
                protocol_version=1,
                kind="accepted",
                sequence=1,
                run_id=start.run_id,
                attempt_id=start.attempt_id,
                request_id=start.request_id,
            )
        )
    )
    return session


def test_host_rejects_wrong_identity_stale_revision_and_duplicates(start: StartFrame) -> None:
    result = result_frame(start)
    with pytest.raises(ValueError):
        conversation(start).accept(
            encode_worker_frame(result.model_copy(update={"attempt_id": "old"}))
        )
    stale = replace(result.result, request=replace(result.result.request, revision=6))
    with pytest.raises(ValueError):
        conversation(start).accept(encode_worker_frame(result.model_copy(update={"result": stale})))
    session = conversation(start)
    session.accept(encode_worker_frame(result))
    with pytest.raises(ValueError):
        session.accept(encode_worker_frame(result))


def test_result_after_cancel_is_not_accepted(start: StartFrame) -> None:
    session = conversation(start)
    assert isinstance(session.cancellation(), CancelFrame)
    with pytest.raises(ValueError):
        session.cancellation()
    with pytest.raises(ValueError):
        session.accept(encode_worker_frame(result_frame(start)))


def test_cancellation_confirmation_requires_host_request(start: StartFrame) -> None:
    frame = CancelledFrame(
        protocol_version=1,
        kind="cancelled",
        sequence=2,
        run_id=start.run_id,
        attempt_id=start.attempt_id,
        request_id=start.request_id,
    )
    with pytest.raises(ValueError):
        conversation(start).accept(encode_worker_frame(frame))
    session = conversation(start)
    session.cancellation()
    assert isinstance(session.accept(encode_worker_frame(frame)), CancelledFrame)


def execute(start: StartFrame, extra: bytes = b"") -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, "-m", "wb_tool.worker"],
        input=encode_worker_frame(start) + extra,
        cwd=Path(start.source_path).parent,
        capture_output=True,
        timeout=30,
        check=False,
    )


def test_real_worker_analytical_result(start: StartFrame) -> None:
    process = execute(start)
    assert process.returncode == 0, process.stderr
    frames = process.stdout.splitlines()
    assert len(frames) == 3 and not process.stderr
    session = WorkerConversation(start)
    for data in frames:
        session.accept(data)
    frame = parse_worker_frame(frames[-1])
    assert isinstance(frame, ResultFrame)
    assert frame.result.lanes[0].bands[0].signal == 10
    assert frame.result.request.revision == 7


def test_real_worker_wrong_source_fails(start: StartFrame) -> None:
    changed = start.model_copy(update={"request": replace(start.request, source_sha256="0" * 64)})
    process = execute(changed)
    assert process.returncode == 2
    final = parse_worker_frame(process.stdout.splitlines()[-1])
    assert isinstance(final, FailureFrame) and final.code == "analysis_invalid"


@pytest.mark.parametrize("wrong_identity", [False, True])
def test_real_worker_cancellation(start: StartFrame, wrong_identity: bool) -> None:
    # Real decoding creates time for a queued cancellation, without worker test sleeps.
    path = Path(start.source_path).parent / "large.tif"
    tifffile.imwrite(path, np.full((4096, 4096), 245, dtype=np.uint16))
    image = load_tiff(path)
    changed = start.model_copy(
        update={
            "source_path": str(path),
            "request": replace(start.request, source_sha256=image.sha256),
        }
    )
    cancel = CancelFrame(
        protocol_version=1,
        kind="cancel",
        sequence=1,
        run_id=changed.run_id,
        attempt_id="wrong" if wrong_identity else changed.attempt_id,
        request_id=changed.request_id,
    )
    process = execute(changed, encode_worker_frame(cancel))
    final = parse_worker_frame(process.stdout.splitlines()[-1])
    if wrong_identity:
        assert isinstance(final, FailureFrame) and final.code == "protocol_invalid"
        assert process.returncode == 2
    else:
        assert isinstance(final, CancelledFrame) and process.returncode == 0
    assert not any(
        isinstance(parse_worker_frame(line), ResultFrame) for line in process.stdout.splitlines()
    )


def test_real_worker_malformed_initial_frame(tmp_path: Path) -> None:
    process = subprocess.run(
        [sys.executable, "-m", "wb_tool.worker"],
        input=b"{}\n",
        capture_output=True,
        cwd=tmp_path,
        timeout=10,
        check=False,
    )
    assert process.returncode == 2
    assert isinstance(parse_worker_frame(process.stdout.splitlines()[-1]), ProtocolErrorFrame)


def test_duplicate_json_keys_rejected() -> None:
    with pytest.raises(ValueError, match="重复"):
        parse_worker_frame(b'{"kind":"hello","kind":"hello","protocol_version":1,"sequence":0}')


def test_oversized_frame_rejected() -> None:
    with pytest.raises(ValueError, match="上限"):
        parse_worker_frame(b"x" * (4 * 1024 * 1024 + 1))


def test_out_of_order_result_rejected(start: StartFrame) -> None:
    with pytest.raises(ValueError):
        WorkerConversation(start).accept(encode_worker_frame(result_frame(start)))


def test_real_worker_unterminated_input_rejected(start: StartFrame) -> None:
    process = subprocess.run(
        [sys.executable, "-m", "wb_tool.worker"],
        input=encode_worker_frame(start).rstrip(b"\n"),
        capture_output=True,
        cwd=Path(start.source_path).parent,
        timeout=10,
        check=False,
    )
    assert process.returncode == 2
    assert isinstance(parse_worker_frame(process.stdout.splitlines()[-1]), ProtocolErrorFrame)
