"""Pinned, offline CPU OCR. All models are verified before engine construction."""

from collections.abc import Callable
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
from typing import cast

import numpy as np
from numpy.typing import NDArray

from wb_tool.adapters.tiff_input import load_tiff
from wb_tool.application.analysis import AnalysisCancelled
from wb_tool.domain.worksheet import OCRRecognition, TextBounds, TextToken

MODEL_HASHES = (
    ("PP-OCRv6_det_small.onnx", "090f04abcd9d9a7498bc4ebf677e4cb9bdce1fe4197ddb7e529f1ef44e1ff94f"),
    ("PP-OCRv6_rec_small.onnx", "6f327246b50388f3c176ae304bd95767ea6dc0c9ae92153ef8cbe210b3c14884"),
    (
        "ch_ppocr_mobile_v2.0_cls_mobile.onnx",
        "e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c",
    ),
)


def verify_ocr_models(directory: Path) -> tuple[tuple[str, str], ...]:
    for name, expected in MODEL_HASHES:
        path = directory / name
        if not path.is_file() or path.is_symlink():
            raise ValueError("OCR 模型缺失：" + name)
        digest = sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected:
            raise ValueError("OCR 模型摘要不符：" + name)
    return MODEL_HASHES


def recognize_figure(
    source: str | Path,
    expected_sha256: str,
    *,
    cancelled: Callable[[], bool] | None = None,
) -> OCRRecognition:
    if cancelled is not None and cancelled():
        raise AnalysisCancelled()
    # Optional dependency import is deliberately inside the OCR operation only.
    import rapidocr
    from rapidocr import RapidOCR
    from rapidocr.utils.output import RapidOCROutput

    if version("rapidocr") != "3.9.2" or version("onnxruntime") != "1.31.0":
        raise ValueError("OCR 引擎版本不符；请修复安装")
    models = Path(rapidocr.__file__).parent / "models"
    hashes = verify_ocr_models(models)
    image = load_tiff(source)
    if image.sha256 != expected_sha256:
        raise ValueError("OCR 输入快照摘要不符")
    height, width = image.pixels.shape
    display = (image.pixels // 257).astype(np.uint8) if image.bit_depth == 16 else image.pixels
    engine = RapidOCR(
        params={
            "Global.log_level": "error",
            "Global.max_side_len": 4096,
            "EngineConfig.onnxruntime.intra_op_num_threads": 1,
            "EngineConfig.onnxruntime.inter_op_num_threads": 1,
            "Det.model_path": str(models / MODEL_HASHES[0][0]),
            "Rec.model_path": str(models / MODEL_HASHES[1][0]),
            "Cls.model_path": str(models / MODEL_HASHES[2][0]),
        }
    )
    tokens: list[TextToken] = []

    def starts(length: int) -> tuple[int, ...]:
        last = max(0, length - 2048)
        return tuple(sorted({*range(0, last + 1, 1792), last}))

    xs, ys = starts(width), starts(height)
    if len(xs) * len(ys) > 64:
        raise ValueError("OCR 图像超出64分块预算；请拆分 Fig")
    for y in ys:
        for x in xs:
            if cancelled is not None and cancelled():
                raise AnalysisCancelled()
            tile = display[y : y + 2048, x : x + 2048]
            output = engine(tile)
            if not isinstance(output, RapidOCROutput):
                raise ValueError("OCR 引擎未返回完整识别输出")
            if output.boxes is None or output.txts is None or output.scores is None:
                continue
            boxes = cast(NDArray[np.float32], output.boxes)
            if boxes.ndim != 3 or boxes.shape[1:] != (4, 2):
                raise ValueError("OCR 坐标形状无效")
            if len(boxes) != len(output.txts) or len(boxes) != len(output.scores):
                raise ValueError("OCR 文字与坐标数量不一致")
            for box, text, score in zip(boxes, output.txts, output.scores, strict=True):
                if not bool(np.isfinite(box).all()):
                    raise ValueError("OCR 坐标包含非有限值")
                bounds = TextBounds(
                    x + max(0.0, float(np.min(box[:, 0]))),
                    y + max(0.0, float(np.min(box[:, 1]))),
                    min(float(width), x + float(np.max(box[:, 0]))),
                    min(float(height), y + float(np.max(box[:, 1]))),
                )
                tokens.append(TextToken("candidate", text, bounds, float(score)))
    selected: list[TextToken] = []
    for token in sorted(tokens, key=lambda token: token.confidence, reverse=True):
        duplicate = False
        for previous in selected:
            a, b = token.bounds, previous.bounds
            overlap = max(0.0, min(a.x1, b.x1) - max(a.x0, b.x0)) * max(
                0.0, min(a.y1, b.y1) - max(a.y0, b.y0)
            )
            area = min((a.x1 - a.x0) * (a.y1 - a.y0), (b.x1 - b.x0) * (b.y1 - b.y0))
            if token.text == previous.text and overlap / area > 0.5:
                duplicate = True
                break
        if not duplicate:
            selected.append(token)
    ordered = sorted(selected, key=lambda token: (token.bounds.y0, token.bounds.x0, token.text))
    tokens = [
        TextToken(f"T{index + 1:05d}", token.text, token.bounds, token.confidence)
        for index, token in enumerate(ordered)
    ]
    if cancelled is not None and cancelled():
        raise AnalysisCancelled()
    return OCRRecognition(
        image.sha256,
        width,
        height,
        tuple(tokens),
        "rapidocr@3.9.2/ppocrv6/onnxruntime@1.31.0",
        hashes,
        preprocess_id="ocr_u16_div257_tiles2048_overlap256@1",
    )
