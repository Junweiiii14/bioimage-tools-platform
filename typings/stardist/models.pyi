import numpy as np
from numpy.typing import NDArray

class StarDist2D:
    def __init__(self, config: None, *, name: str, basedir: str) -> None: ...
    def predict_instances(
        self,
        img: NDArray[np.float32],
        *,
        axes: str,
        scale: float,
        n_tiles: tuple[int, int],
        show_tile_progress: bool,
    ) -> tuple[NDArray[np.generic], object]: ...
