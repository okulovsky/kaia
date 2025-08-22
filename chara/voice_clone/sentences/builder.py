import os
import shutil
from pathlib import Path
from foundation_kaia.misc import Loc
from .corpus_filter import ICorpusFilter
from brainbox import BrainBox
from brainbox.deciders import EspeakPhonemizer, Collector
from yo_fluq import *
import pandas as pd
from ...tools import Language, LanguageToDecider
from .algorithm import GoldenSetAlgorithm
from nltk import word_tokenize
import nltk
from nltk.tokenize import sent_tokenize
import hashlib

class Locations:
    def __init__(self, folder):
        self.folder = folder

    @property
    def source(self) -> Path:
        return self.folder/'source.json'

    @property
    def phonemization_command(self) -> Path:
        return self.folder/'pronemization_command.json'

    @property
    def phonemized_dataset(self) -> Path:
        return self.folder/'prohemized_dataset.json'

    def reset(self):
        shutil.rmtree(self.folder, ignore_errors=True)
        os.makedirs(self.folder)


class UpsamplingDatasetBuilder:
    def __init__(self,
                 name: str,
                 language: Language,
                 location: Path|None = Loc.data_folder/'upsampling_dataset',
                 ):
        self.locations = Locations(location/name)
        self.language = language
        self.filters: list[ICorpusFilter] = []
        self.target_sentence_count: int = 50
        self.ban_sentences_id: list[str] = []
        self.ban_words: list[str] = []


    def create_source_text(self, texts: Iterable[str]):
        if self.locations.source.is_file():
            return
        if len(self.language.allowed_symbols) <= 1:
            raise ValueError("Fill allowed symbols for the language")
        if len(self.filters) == 0:
            raise ValueError("Fill filters")
        try:
            sent_tokenize('First sentence. Second sentence.')
        except:
            nltk.download("punkt")
        lines = []
        for text in Query.en(texts).feed(fluq.with_progress_bar()):
            if text is None:
                continue
            sentences = sent_tokenize(text)
            for sentence in sentences:
                for filter in self.filters:
                    sentence = filter.filter(sentence)
                    if sentence is None:
                        break
                if sentence is not None:
                    lines.append(sentence)
        FileIO.write_json(lines, self.locations.source)


    def create_phonemize_command(self) -> BrainBox.Command:
        source = FileIO.read_json(self.locations.source)
        builder = Collector.TaskBuilder()
        for i, partition in Query.en(source).feed(fluq.partition_by_count(1000)).feed(enumerate):
            builder.append(
                BrainBox.Task.call(EspeakPhonemizer).phonemize(
                    partition,
                    language=LanguageToDecider.map(self.language, EspeakPhonemizer)
                ),
                dict(sentences=partition)
            )
        task = builder.to_collector_pack('to_array')
        return BrainBox.Command(task).with_cache(self.locations.phonemization_command)


    def preprocess_phonemization_samples_data(self, batches_count: int = 5):
        phonemization_result = BrainBox.Command.Cache(self.locations.phonemization_command).get_cached_result()
        data = {}
        for i, item in enumerate(phonemization_result):
            if i > batches_count:
                break
            for sentence, p_sentence in zip(item['tags']['sentences'], item['result']):
                words = word_tokenize(sentence)
                clean_words = []
                for word in words:
                    ok = True
                    for c in word:
                        if c not in self.language.words_symbols:
                            ok = False
                            break
                    if ok:
                        clean_words.append(word)
                if len(clean_words) != len(p_sentence):
                    continue
                for word, p_word in zip(clean_words, p_sentence):
                    for p in p_word:
                        if p not in data:
                            data[p] = set()
                        data[p].add((word, ' '.join(p_word)))
        return data

    def create_phonemization_samples(self, preprocessed_phonemization_samples_data, samples_per_phoneme: int = 5):
        data = preprocessed_phonemization_samples_data
        rows = []
        for key in data:
            samples = list(data[key])
            rows.append([key, len(samples)])
            for i in range(samples_per_phoneme):
                if i >= len(samples):
                    rows[-1].append('')
                else:
                    rows[-1].append(samples[i])
        columns = ['phoneme', 'count'] + [str(i) for i in range(samples_per_phoneme)]
        return pd.DataFrame(rows, columns=columns).sort_values('count', ascending=False).reset_index(drop=True)

    def postprocess_phonemization(self):
        data = BrainBox.Command.Cache(self.locations.phonemization_command).get_cached_result()
        result = {}
        for batch in data:
            for sentence, sentence_phonemes in zip(batch['tags']['sentences'], batch['result']):
                stats = {}
                for word_phonemes in sentence_phonemes:
                    for phoneme in word_phonemes:
                        stats[phoneme] = stats.get(phoneme, 0) + 1
                code = hashlib.sha256(sentence.encode()).hexdigest()[:24]
                result['id_' + code] = dict(
                    sentence=sentence,
                    stats=stats
                )
        FileIO.write_json(result, self.locations.phonemized_dataset)

    def run_algorithm(self):
        data = FileIO.read_json(self.locations.phonemized_dataset)
        allowed_phonemes = set(self.language.native_espeak_phonemes)
        fixed_data = {}
        for id, item in data.items():
            item['stats'] = {k: v for k, v in item['stats'].items() if k in allowed_phonemes}
            fixed_data[id] = item

        algorithm = GoldenSetAlgorithm(fixed_data)
        result = algorithm.run(self.target_sentence_count, self.ban_sentences_id, self.ban_words)
        return result

    def get_statistics_frame(self, result):
        df_rows = []
        for item in result:
            row = dict(ind=item['index'])
            for key, value in item['sentence']['stats'].items():
                row[key] = value
            df_rows.append(row)
        df = pd.DataFrame(df_rows).fillna(0)
        return df

    @staticmethod
    def write(result, file):
        (
            Query
            .en(result)
            .select(lambda z: f"{z['index']} {z['id']}: {z['sentence']['sentence']}")
            .to_text_file(file)
        )

    @staticmethod
    def read(file):
        return (
            Query
            .file.text(file, encoding='utf-8')
            .select(lambda z: z.split(':'))
            .select(lambda z: dict(index=z[0].split(' ')[0], id=z[0].split(' ')[1], text=z[1].strip()))
            .to_list()
        )

    @staticmethod
    def get_sentences_from_file(file):
        data = UpsamplingDatasetBuilder.read(file)
        return Query.en(data).select(lambda z: z['text'].replace(' .','.').strip()).where(lambda z: z!='').distinct(lambda z: z.lower()).to_list()




