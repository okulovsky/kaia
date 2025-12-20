from chara.common import CharaApis, BrainBoxCache, ICache, BrainBoxUnit, logger
from brainbox import BrainBox
from brainbox.deciders import Resemblyzer
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping, Sequence
import numpy as np


@dataclass(frozen=True)
class CandidateMatch:
    candidate_path: Path
    best_distance: float        # 1 - cosine_similarity, меньше = лучше
    best_etalon: Path           # (я назвал без "s", т.к. один лучший эталон)


def prepare_normalized_vectors(
    vectors: Mapping[Path, Sequence[float]]
) -> Dict[Path, np.ndarray]:
    """
    Переводим dict[Path, list[float]] -> dict[Path, np.ndarray]
    и нормализуем до единичной длины (для косинусной метрики).
    """
    normed: Dict[Path, np.ndarray] = {}

    for path, coords in vectors.items():
        v = np.asarray(coords, dtype=float)
        norm = np.linalg.norm(v)
        if norm == 0.0:
            raise ValueError(f"Zero-norm vector for {path}")
        normed[path] = v / norm

    return normed


def _compute_candidate_matches(
    etalon: Dict[int, List[Path]],
    candidates: Dict[Path, int],
    vectors: Mapping[Path, Sequence[float]],
) -> dict[Path,CandidateMatch]:
    """
    etalon:     модель -> список эталонных файлов
    candidates: инференсный файл -> модель
    vectors:    файл -> embedding (list[float])

    1) Переводим vectors в dict[Path, np.ndarray] и нормализуем.
    2) Для каждого candidate ищем лучший эталон по косинусной дистанции.
    """
    # 1. Преобразуем во float ndarrays, нормализуем
    normed_vectors = prepare_normalized_vectors(vectors)

    results: dict[Path, CandidateMatch] = {}

    for candidate_path, model_id in candidates.items():
        if model_id not in etalon:
            raise KeyError(f"No etalon files registered for model_id={model_id}")
        if candidate_path not in normed_vectors:
            raise KeyError(f"No vector found for candidate file {candidate_path!s}")

        cand_vec = normed_vectors[candidate_path]

        best_dist = float("inf")
        best_etalon_path: Path | None = None

        for etalon_path in etalon[model_id]:
            if etalon_path not in normed_vectors:
                raise KeyError(f"No vector found for etalon file {etalon_path!s}")

            etalon_vec = normed_vectors[etalon_path]

            # Косинусная схожесть = dot(нормированные)
            sim = float(np.dot(cand_vec, etalon_vec))
            dist = 1.0 - sim

            if dist < best_dist:
                best_dist = dist
                best_etalon_path = etalon_path

        if best_etalon_path is None:
            raise RuntimeError(f"No etalon candidates for model_id={model_id}")

        results[candidate_path] = CandidateMatch(
                candidate_path=candidate_path,
                best_distance=best_dist,
                best_etalon=best_etalon_path,
            )

    return results

class VoiceSimilarityCache(ICache[dict[Path,CandidateMatch]]):
    def __init__(self, work_folder: Path|None = None):
        super().__init__(work_folder)
        self.encodings = BrainBoxCache[Path,list[float]]()


    def _create_task(self, path: Path):
        return BrainBox.Task.call(Resemblyzer).vector(path.name)


    def pipeline(self,
                 etalon: dict[int,list[Path]],
                 candidates: dict[Path, int],
                 ):

        @logger.phase(self.encodings)
        def _():
            unit = BrainBoxUnit(self._create_task)
            e_files = [p for lst in etalon.values() for p in lst ]
            for e in e_files:
                CharaApis.brainbox_api.upload(e.name, e)
            unit.run(
                self.encodings,
                e_files + list(candidates)
            )

        vectors = {case: option['vector'] for case, option in self.encodings.read_cases_and_single_options()}

        result = _compute_candidate_matches(
            etalon,
            candidates,
            vectors
        )

        self.write_result(result)





