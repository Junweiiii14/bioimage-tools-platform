"""Reproduce P001's old public API/real-worker baseline in a new scratch directory."""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import tifffile
from pydantic import TypeAdapter
from wb_tool.api import (
    AnalysisRequest,
    AnalysisResult,
    BandAnnotation,
    BandBounds,
    LaneAnnotation,
    LaneROI,
    ResultFrame,
    StartFrame,
    WorkerConversation,
    analyze_annotations,
    encode_worker_frame,
    load_tiff,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir()  # Refuse any existing result directory.
    design = json.loads(Path(__file__).with_name("frozen-case-design.json").read_text("utf-8"))
    adapter = TypeAdapter(AnalysisResult)
    records = []
    for case in design["cases"]:
        source = output / (case["name"] + ".tif")
        pixels = np.repeat(np.array(case["profile"], dtype=case["dtype"])[:, None], 3, axis=1)
        tifffile.imwrite(source, pixels, metadata=None)
        image = load_tiff(source)
        request = AnalysisRequest(
            image.sha256,
            0,
            "light",
            (
                LaneAnnotation(
                    LaneROI("sample-1", *case["roi"]),
                    (BandAnnotation("band-1", BandBounds(0, 4)),),
                ),
            ),
        )
        direct = analyze_annotations(image, request)
        start = StartFrame(
            protocol_version=1,
            kind="start",
            sequence=0,
            run_id=case["name"],
            attempt_id="baseline-1",
            request_id="frozen-1",
            source_path=str(source),
            request=request,
        )
        child = subprocess.Popen(
            [sys.executable, "-m", "wb_tool.worker"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            stdout, stderr = child.communicate(encode_worker_frame(start), timeout=20)
        except subprocess.TimeoutExpired:
            child.kill()
            child.communicate()
            raise
        if child.returncode != 0:
            raise RuntimeError((child.returncode, stderr))
        conversation = WorkerConversation(start)
        frames = [conversation.accept(line) for line in stdout.splitlines()]
        last = frames[-1]
        if not isinstance(last, ResultFrame):
            raise RuntimeError("Missing result")
        actual = last.result.lanes[0].bands[0]
        if (actual.status, actual.signal) != (case["expected_status"], case["expected_signal"]):
            raise AssertionError((case, actual))
        result_bytes = adapter.dump_json(last.result)
        if adapter.dump_json(direct) != result_bytes:
            raise AssertionError("Public API and real worker differ")
        if hashlib.sha256(source.read_bytes()).hexdigest() != image.sha256:
            raise AssertionError("Original input changed")
        (output / (case["name"] + ".result.json")).write_bytes(result_bytes)
        records.append(
            {
                "case": case["name"],
                "source_sha256": image.sha256,
                "result_sha256": hashlib.sha256(result_bytes).hexdigest(),
                "observed_pid": child.pid,
                "exit_code": child.returncode,
                "frames": [frame.kind for frame in frames],
                "status": actual.status,
                "signal": actual.signal,
                "independent_expected": case["expected_signal"],
                "matches_direct_api": True,
            }
        )
    (output / "observed.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
