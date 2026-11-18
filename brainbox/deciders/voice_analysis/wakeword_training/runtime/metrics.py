"""Metrics computed from measured scores, with explicit exposure units."""

import numpy as np


def valid_scores(values):
    values = np.asarray(values)
    if values.ndim != 1 or not len(values):
        raise ValueError("scores must be nonempty vectors")
    for offset in range(0, len(values), 65536):
        chunk = values[offset : offset + 65536]
        if not np.isfinite(chunk).all() or (chunk < 0).any() or (chunk > 1).any():
            raise ValueError("scores must be finite probabilities")
    return values


def positive_count(values, threshold):
    return sum(
        int(np.count_nonzero(values[i : i + 65536] >= threshold))
        for i in range(0, len(values), 65536)
    )


def calculate_metrics(positive, negative, background, threshold, frames, frame_step):
    positive, negative, background = map(valid_scores, (positive, negative, background))
    if not np.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("invalid threshold")
    if frames <= 0 or frame_step != 0.08:
        raise ValueError("zero/invalid exposure")
    tp = positive_count(positive, threshold)
    fp = positive_count(negative, threshold)
    fn = len(positive) - tp
    tn = len(negative) - fp
    bg = positive_count(background, threshold)
    hours = frames * frame_step / 3600
    return {
        "threshold": threshold,
        "supervised": {
            "positive_count": len(positive),
            "negative_count": len(negative),
            "TP": tp,
            "FP": fp,
            "TN": tn,
            "FN": fn,
            "recall": tp / len(positive),
            "precision": tp / (tp + fp) if tp + fp else None,
            "F1": 2 * tp / (2 * tp + fp + fn),
            "accuracy": (tp + tn) / (len(positive) + len(negative)),
        },
        "background": {
            "positive_windows": bg,
            "total_windows": len(background),
            "feature_frames": frames,
            "frame_step_seconds": frame_step,
            "feature_equivalent_hours": hours,
            "threshold_windows_per_feature_hour": bg / hours,
            "stride": 1,
            "window_policy": "segmented-stride1-v1",
            "waveform_hours": None,
        },
        "unavailable_values": {
            "waveform_hours": "original waveform duration is not measured",
            **({"precision": "TP+FP=0"} if not tp + fp else {}),
        },
    }
