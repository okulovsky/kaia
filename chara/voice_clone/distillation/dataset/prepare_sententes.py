from typing import Iterable
from itertools import tee
from chara import Chara, Language, logger, brainbox_pipeline
from chara.common.pipelines.brainbox.brainbox_pipeline import BrainBoxResult
from .common import create_phonemization_samples, Phonemization
from .corpus import Corpus
from .algorithm import AlgorithmData
from brainbox.deciders import EspeakPhonemizer
import json
from pathlib import Path
import hashlib

def _iterate_dataset(path: Path):
    with open(path, 'r') as file:
        for line in file:
            yield json.loads(line)

def _iterate_tasks(path: Path, language: Language):
    for array in _iterate_dataset(path):
        yield EspeakPhonemizer.new_task(info=array).phonemize_to_file(array, language.espeak_name)

def _iterate_phonemizations(bbox_result: BrainBoxResult):
    for result in bbox_result.read_successes():
        phonemizations = json.loads(result.result.read_text())
        for line, phonemization in zip(result.task_info, phonemizations):
            yield Phonemization(
                id=hashlib.md5(line.encode("utf-8")).hexdigest()[:20],
                text=line,
                phonemization=phonemization
            )

def prepare_sentences(raw_dataset: Iterable[str], corpus: Corpus, language: Language):
    source_1, source_2 = tee(raw_dataset)

    @Chara.phase
    def counting_records_in_corpus():
        count = 0
        for _ in source_1:
            count += 1
        logger.log(f"{count} sentences in the dataset in the source dataset")
        return count

    count = Chara.previous.result

    @Chara.phase
    def filtering_corpus():
        path = Chara.current.folder / 'tmp.jsonlines'
        corpus.create(source_2, path, count)
        lines_count = 0
        packages_count = 0

        for array in _iterate_dataset(path):
            lines_count += len(array)
            packages_count += 1

        logger.log(f"{lines_count} sentences in the dataset in {packages_count} packages")
        if lines_count == 0 or packages_count == 0:
            raise ValueError("No lines in the dataset.")

        return path

    path = Chara.previous.result
    result = Chara.call(brainbox_pipeline)(_iterate_tasks(path, language), result_to_file=True)
    data = list(_iterate_phonemizations(result))

    @Chara.phase
    def reference_table():
        samples_df = create_phonemization_samples(language, data)
        logger.log("Reference table:")
        logger.log(samples_df)
        logger.log(list(samples_df.phoneme))
        logger.log(f"{len(data)} sentences are phonemized")
        return samples_df

    dataset = AlgorithmData.from_phonemizations(
        data,
        language
    )
    return dataset
