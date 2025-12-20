import numpy as np
from .read_and_write import WavInfo

def slice_wav_by_seconds(
    data: np.ndarray,
    info,
    sl: slice
) -> np.ndarray:
    """
    Slice WAV data by time in seconds.

    Rules:
        wav[start:end], where start/end are:
            - float/int: seconds
            - negative -> seconds from end
            - None -> start or end of file
        step is not supported.

    Returns: (new_data, new_info)
    """

    if not isinstance(sl, slice):
        raise TypeError("Slice must be a slice object, e.g. wav[start:end]")

    if sl.step not in (None, 1):
        raise TypeError("Step is not supported in Wav slicing")

    sr = info.frame_rate
    n_frames = data.shape[0]

    def sec_to_index(val, default_if_none: int) -> int:
        """
        Convert a second-based slice boundary into a frame index.
        Supports negative seconds (from end).
        """
        if val is None:
            idx = default_if_none
        else:
            if not isinstance(val, (int, float)):
                raise TypeError("Slice start/end must be numbers or None")
            frames = int(round(val * sr))
            if frames < 0:
                # Negative → from end
                idx = n_frames + frames
            else:
                idx = frames

        # Clamp
        if idx < 0:
            idx = 0
        elif idx > n_frames:
            idx = n_frames

        return idx

    start_f = sec_to_index(sl.start, 0)
    stop_f = sec_to_index(sl.stop, n_frames)

    if stop_f < start_f:
        stop_f = start_f

    new_data = data[start_f:stop_f, :]

    # Создаём новый info (frame count не храним внутри)
    new_info = type(info)(
        n_channels=info.n_channels,
        sample_width=info.sample_width,
        frame_rate=info.frame_rate,
        comptype=info.comptype,
        compname=info.compname,
    )

    return new_data