"""P014 frozen method; changing any numerical setting requires a new version."""

from nuclei_tool.domain.runtime import RUNTIME_VERSIONS

METHOD_VERSION = "stardist-fluo-p014@1"
MODEL_NAME = "2D_versatile_fluo"
MODEL_FILES = {
    "config.json": "836da16282c3e0db1ba2e58f377e977419887ace8c737ebde16a094d58d50f74",
    "thresholds.json": "5cd6aac6e923f8659b63a9e297485920d45a59dad35371ddb8b6ae4be398d805",
    "weights_best.h5": "42202bd269c8106782316f1a2c75afb3f5ffa65e525c2e155ee0ced3a95da349",
}
RESEARCH_VERSIONS = {
    "stardist": "0.9.2",
    "csbdeep": "0.8.2",
    "tensorflow-cpu": "2.21.0",
    "keras": "3.15.1",
    "numpy": "2.5.4",
    "scipy": "1.18.1",
    "pillow": "13.0.0",
}
# Engineering admission budget, not an accuracy or memory guarantee.
# P014's largest validated frame was 1024 x 1360 (1,392,640 pixels).
MAX_PIXELS = 2_000_000
MAX_INPUT_BYTES = 16 * 1024 * 1024


def method_description() -> dict[str, object]:
    return {
        "method_version": METHOD_VERSION,
        "readiness": "research_not_scientifically_admitted",
        "model": MODEL_NAME,
        "model_sha256": dict(MODEL_FILES),
        "runtime_versions": dict(RUNTIME_VERSIONS),
        "scale": 0.5,
        "normalization_percentiles": [3, 99.8],
        "normalization_clip": False,
        "tiles_yx": [2, 2],
        "cpu_threads": [4, 1],
        "probability_threshold": 0.479071463157368,
        "nms_threshold": 0.3,
        "coordinate_convention": "integer_pixel_centres_yx@1",
    }
