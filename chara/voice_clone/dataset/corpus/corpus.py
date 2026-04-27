from ....common import JsonlCache, logger
from .filters import ICorpusFilter
from pathlib import Path
from yo_fluq import *
import nltk

class Corpus:
    def __init__(self,
                 filters: Iterable[ICorpusFilter],
                 lines_in_batch: int = 10000
                 ):
        self.filters = tuple(filters)
        self.lines_in_batch = lines_in_batch

    def _iterate(self, reader: Iterable[str], count: int|None) -> Iterable[str]:
        try:
            nltk.sent_tokenize('First sentence. Second sentence.')
        except:
            nltk.download("punkt_tab")

        rejections = [0 for _ in self.filters]
        successes = 0

        for line in Query.en(reader).feed(fluq.with_progress_bar(total=count)):
            line = line.strip()
            for sentence in nltk.sent_tokenize(line):
                for index, filter in enumerate(self.filters):
                    sentence = filter.filter(sentence)
                    if sentence is None:
                        rejections[index] += 1
                        break
                if sentence is not None:
                    yield sentence
                    successes += 1
        for index, rejection in enumerate(rejections):
            logger.log(f"{rejection} items rejected by filter {index}")
        logger.log(f"{successes} sentences produced")

    def create(self, reader: Iterable[str], target_file: JsonlCache, lines_count: int|None = None):
        with target_file.session():
            it = Query.en(self._iterate(reader, lines_count)).feed(fluq.partition_by_count(self.lines_in_batch))
            for batch in it:
                target_file.write(batch)



