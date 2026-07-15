from typing import Iterable
from chara import Chara, Language
from ..distillation.dataset import AlgorithmDatasetPipeline


def dataset_algorithm(
        language: Language,
        samples_per_batch: int = 100,
        exit_count: int = 100,
        banned_words: Iterable[str] = (),
        ):
    folder = Chara.Apis.content_folder / 'voice_clone_dataset' / language.code / '$algorithm'
    Chara.start(folder)
    pipeline = AlgorithmDatasetPipeline(language, samples_per_batch, exit_count, banned_words)
    return Chara.call(pipeline)()
