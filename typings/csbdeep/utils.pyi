import numpy as np
from numpy.typing import NDArray

def normalize(
    x: NDArray[np.uint8], pmin: float, pmax: float, axis: None, clip: bool
) -> NDArray[np.float32]: ...
