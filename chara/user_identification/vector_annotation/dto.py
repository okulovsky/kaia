from dataclasses import dataclass, field
from chara.common.pipelines.annotation.core import IAnnotationCase
from abc import abstractmethod
import numpy as np
from typing import TypeVar


class IVectorAnnotationCase(IAnnotationCase):
    @abstractmethod
    def get_vector(self) -> np.ndarray:
        pass


TCase = TypeVar('TCase', bound=IVectorAnnotationCase)


@dataclass
class VectorSample:
    vector: np.ndarray
    id: str


@dataclass(eq=False)
class VectorClass:
    name: str
    samples: list[VectorSample]
    center: np.ndarray | None
    sigma: float

    @classmethod
    def build(cls, name: str, samples: list[VectorSample]) -> 'VectorClass':
        if not samples:
            return cls(name=name, samples=[], center=None, sigma=0.0)
        vectors = np.array([s.vector for s in samples])
        center = vectors.mean(axis=0)
        distances = np.linalg.norm(vectors - center, axis=1)
        sigma = float(distances.std()) if len(vectors) > 1 else 0.0
        return cls(name=name, samples=samples, center=center, sigma=sigma)


@dataclass
class CurrentState:
    free_vectors: list[VectorSample]
    classes: dict[str, VectorClass]
    class_names: tuple[str, ...]
