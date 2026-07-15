from typing import Iterable
import json
from chara import Chara, Language, logger
from .common import AnnotationCase, Phonemization
from .algorithm import AlgorithmData
from .algorithm_annotation_step import algorithm_annotation_step


class AlgorithmDatasetPipeline:
    def __init__(self,
                 language: Language,
                 samples_per_batch: int = 100,
                 exit_count: int = 100,
                 banned_words: Iterable[str] = (),
                 ):
        self.language = language
        self.samples_per_batch = samples_per_batch
        self.exit_count = exit_count
        self.banned_words = set(banned_words)

    def __call__(self):
        root_folder = Chara.current.folder
        preview_dataset_path = root_folder.parent / '$preview' / 'dataset.jsonlines'

        @Chara.phase
        def loading_dataset():
            phonemizations = []
            with open(preview_dataset_path, 'r') as file:
                for line in file:
                    row = json.loads(line)
                    phonemizations.append(Phonemization(row['id'], row['text'], row['phonemization']))
            return AlgorithmData.from_phonemizations(phonemizations, self.language)

        data: AlgorithmData = Chara.previous.result

        annotations: list[AnnotationCase] = []
        ready: list[str] = []
        while True:
            addition = Chara.call(algorithm_annotation_step)(data, annotations, self.samples_per_batch, self.banned_words)
            annotations.extend(addition)
            ready = [case.text for case in annotations if case.accepted]
            logger.info(f"Available {len(ready)} sentences")
            if len(ready) > self.exit_count:
                break

        result_path = root_folder.parent / 'dataset.json'
        result_path.write_text(json.dumps(
            [dict(id=case.id, text=case.text, accepted=case.accepted) for case in annotations],
            indent=2,
            ensure_ascii=False
        ))

        return ready
