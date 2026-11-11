"""Validate target recognition before cropping; no model dependencies."""

import itertools
import math
import re
from dataclasses import dataclass


class RejectedAudio(ValueError):
    def __init__(self, reason, message):
        super().__init__(message)
        self.reason = reason


def words(text):
    return tuple(re.findall(r"\w+", text.casefold()))


@dataclass
class Crop:
    start: float
    end: float
    confidence: float
    recognition: list[dict]


def _distance(left, right):
    row = list(range(len(right) + 1))
    for i, a in enumerate(left, 1):
        following = [i]
        for j, b in enumerate(right, 1):
            following.append(min(following[-1] + 1, row[j] + 1, row[j - 1] + (a != b)))
        row = following
    return row[-1]


def verify(
    target, recognition, duration, prefix, suffix, threshold=0.7, allowed_variants=None
):
    if not recognition:
        raise RejectedAudio("word_not_found", "Vosk recognized nothing")
    if not isinstance(recognition, list) or any(
        not isinstance(item, dict) or not isinstance(item.get("word"), str)
        for item in recognition
    ):
        raise RejectedAudio("processing_failed", "Vosk returned invalid word records")
    if not math.isfinite(duration) or duration <= 0:
        raise RejectedAudio("invalid_audio", "invalid source duration")
    wanted = words(target)
    candidates = []
    # Preserve the original bounded prefix/suffix trimming policy.
    for first in range(min(len(recognition), len(prefix.split()) + 2)):
        for trim in range(min(len(recognition), len(suffix.split()) + 2)):
            end = len(recognition) - trim
            selected = recognition[first:end]
            if selected:
                recognized = words(" ".join(item["word"] for item in selected))
                distance = _distance("".join(wanted), "".join(recognized))
                candidates.append((distance, first, end, selected, recognized))
    if not candidates:
        raise RejectedAudio("word_not_found", "target word was not found")
    distance, first, end, selected, recognized = min(
        candidates, key=lambda candidate: candidate[0]
    )
    permitted = {words(value) for value in (allowed_variants or [target])}
    if distance > 3 or recognized not in permitted:
        raise RejectedAudio(
            "word_not_found",
            "closest recognized slice is not a permitted target variant",
        )
    confidence = []
    for item in selected:
        value = item.get("conf")
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not 0 <= value <= 1
        ):
            raise RejectedAudio(
                "missing_confidence", "invalid or missing Vosk confidence"
            )
        confidence.append(value)
    minimum = min(confidence)
    if minimum < threshold:
        raise RejectedAudio("low_confidence", f"confidence {minimum} < {threshold}")
    try:
        for item in recognition:
            start, stop = item["start"], item["end"]
            if not (
                math.isfinite(start)
                and math.isfinite(stop)
                and 0 <= start < stop <= duration
            ):
                raise ValueError("invalid word times")
        if any(
            left["end"] > right["start"]
            for left, right in itertools.pairwise(recognition)
        ):
            raise ValueError("overlapping or unordered words")
        start = (
            0
            if first == 0
            else (recognition[first - 1]["end"] + selected[0]["start"]) / 2
        )
        stop = (
            duration
            if end == len(recognition)
            else (selected[-1]["end"] + recognition[end]["start"]) / 2
        )
        if not 0 <= start < stop <= duration:
            raise ValueError("invalid crop")
    except (KeyError, TypeError, ValueError) as error:
        raise RejectedAudio("invalid_crop", str(error)) from error
    return Crop(start, stop, minimum, selected)
