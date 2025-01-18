from typing import *
from frame import Frame

def layer_bufferer(iterable: Iterable[Frame], buffer_size_in_ms, field, maximize: bool = True):
    best_frame = None
    best_value = None
    start = None

    for frame in iterable:
        value = getattr(frame, field)
        if not maximize:
            value = -value
        if start is None or value>best_value:
            best_value = value
            best_frame = frame
            start = frame.timestamp_in_ms

        if frame.timestamp_in_ms - start > buffer_size_in_ms:
            yield best_frame
            start = None
            best_value = None
            best_frame = None






