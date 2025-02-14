import numpy as np
from PIL import Image
from frame import Frame
from typing import Iterable


def layer_comparator(iterable: Iterable[Frame]):
    old_array = None


    for frame in iterable:
        array = np.array(frame.pil_image)

        if old_array is not None:
            frame.simple_comparator_delta = np.mean(np.abs(array - old_array))

        old_array = array