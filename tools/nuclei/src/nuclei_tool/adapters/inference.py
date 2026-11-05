"""Fixed CPU model adapter. Heavy imports occur only in the research worker."""

import os
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from numpy.typing import NDArray

from nuclei_tool.adapters.registration import verify_model, verify_research_environment
from nuclei_tool.domain.method import MODEL_FILES, MODEL_NAME


class NucleiCancelled(Exception):
    """Cooperative stop, distinct from a valid zero-instance image."""


def check_cancelled(cancelled: Callable[[], bool]) -> None:
    if cancelled():
        raise NucleiCancelled


def predict(
    pixels: NDArray[np.uint8],
    model_directory: str,
    cancelled: Callable[[], bool],
    staging_parent: str,
) -> NDArray[np.generic]:
    check_cancelled(cancelled)
    verify_research_environment()
    verify_model(model_directory)
    # Load verified private copies, not mutable user paths after an earlier hash check.
    # Host-owned staging also gets removed when an unresponsive model is killed.
    with TemporaryDirectory(prefix="nuclei-fixed-model-", dir=staging_parent) as temporary:
        model = Path(temporary) / MODEL_NAME
        model.mkdir()
        for name in MODEL_FILES:
            source = Path(model_directory) / name
            with source.open("rb") as incoming, (model / name).open("xb") as outgoing:
                # Fixed model is ~5 MB; refuse an unbounded concurrently replaced member.
                data = incoming.read(16 * 1024 * 1024 + 1)
                if len(data) > 16 * 1024 * 1024:
                    raise ValueError("model_budget: member exceeds 16 MiB")
                outgoing.write(data)
        verify_model(str(model))
        check_cancelled(cancelled)
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
        os.environ["TF_NUM_INTRAOP_THREADS"] = "4"
        os.environ["TF_NUM_INTEROP_THREADS"] = "1"
        os.environ["KERAS_HOME"] = str(Path(temporary) / "keras")
        os.environ["MPLCONFIGDIR"] = str(Path(temporary) / "matplotlib")
        # Minimal local stubs describe the pinned APIs; actual model regression tests
        # run in the separately installed research environment, never desktop deps.
        import tensorflow as tf
        from csbdeep.utils import normalize
        from stardist.models import StarDist2D

        tf.config.threading.set_intra_op_parallelism_threads(4)
        tf.config.threading.set_inter_op_parallelism_threads(1)
        check_cancelled(cancelled)
        network = StarDist2D(None, name=MODEL_NAME, basedir=temporary)
        labels, _ = network.predict_instances(
            normalize(pixels, pmin=3, pmax=99.8, axis=None, clip=False),
            axes="YX",
            scale=0.5,
            n_tiles=(2, 2),
            show_tile_progress=False,
        )
        check_cancelled(cancelled)
        return labels
