import numpy as np
from .dto import VectorSample, VectorClass


def l2(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


def distances_to_classes(vector: np.ndarray, classes: dict[str, VectorClass]) -> list[tuple[str, float]]:
    result = [(name, l2(vector, vc.center)) for name, vc in classes.items() if vc.center is not None]
    result.sort(key=lambda x: x[1])
    return result


def closest_class(vector: np.ndarray, classes: dict[str, VectorClass]) -> str | None:
    ranked = distances_to_classes(vector, classes)
    return ranked[0][0] if ranked else None


def min_dist_to_samples(vector: np.ndarray, samples: list[VectorSample]) -> float:
    if not samples:
        return float('inf')
    return min(l2(vector, s.vector) for s in samples)
