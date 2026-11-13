"""Bounded batches; windows never cross source segment boundaries."""

import numpy as np


def row_batches(array, batch_size):
    for start in range(0, len(array), batch_size):
        yield np.array(array[start : start + batch_size], dtype=np.float32, copy=True)


def window_batches(array, lengths, batch_size):
    batch = np.empty((batch_size, 16, 96), dtype=np.float32)
    count = 0
    offset = 0
    for length in lengths:
        for start in range(max(0, length - 15)):
            batch[count] = array[offset + start : offset + start + 16]
            count += 1
            if count == batch_size:
                yield batch
                batch = np.empty_like(batch)
                count = 0
        offset += length
    if count:
        yield batch[:count]


def sample_batch(arrays, settings, rng):
    counts = settings.batch_counts
    p = arrays["positive_features_train"]
    n = arrays["negative_features_train"]
    bg = arrays["background_train"]
    positive = np.array(
        p[rng.integers(len(p), size=counts["positive"])], dtype=np.float32
    )
    negative = np.array(
        n[rng.integers(len(n), size=counts["adversarial_negative"])], dtype=np.float32
    )
    background = np.empty((counts["background"], 16, 96), dtype=np.float32)
    for i in range(len(background)):
        row = rng.integers(len(bg))
        start = rng.integers(bg.shape[1] - 15)
        background[i] = bg[row, start : start + 16]
    x = np.concatenate([positive, negative, background])
    y = np.concatenate(
        [np.ones(len(positive)), np.zeros(len(negative) + len(background))]
    ).astype(np.float32)
    return x, y
