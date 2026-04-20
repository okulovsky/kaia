from dataclasses import dataclass
from unittest import TestCase
from chara.common.cache import ICache
from chara.paraphrasing.basic_pipelines.utility_pipelines import *
from foundation_kaia.misc import Loc

class VotingCase(IVotingCase):
    def __init__(self, name: str):
        self.name = name
        self.result: str | None = None
        self.vote_group: int | None = None

    def get_result_fingerprint(self) -> str:
        return self.result

class Cache(ICache):
    def __init__(self):
        super().__init__(None)

class Pipeline:
    def __init__(self, results_per_round):
        self.call_count = 0
        self.results_per_round = results_per_round

    def __call__(self, cache: Cache, cases: list[VotingCase]):
        i = self.call_count
        self.call_count += 1
        for case in cases:
            case.result = self.results_per_round[i][case.name]
        cache.write_result(cases)

class ChooseBestAnswerPipelineTest(TestCase):
    def test_majority_vote(self):
        # case 'a' (vote_group 0): rounds produce 'x', 'x', 'y'  → winner 'x'
        # case 'b' (vote_group 1): rounds produce 'p', 'q', 'p'  → winner 'p'
        inner_pipe = Pipeline([
            {'a': 'x', 'b': 'p', 'c': 'x'},
            {'a': 'x', 'b': 'q', 'c': 'y'},
            {'a': 'y', 'b': 'p', 'c': 'z'},
        ])

        with Loc.create_test_folder() as folder:
            cache = UtilityCache(Cache, folder)
            pipe = ChooseBestAnswerPipeline(inner_pipe, poll_size=3)
            pipe(cache, [VotingCase('a'), VotingCase('b'), VotingCase('c')])
            result = cache.read_result()

        self.assertEqual(3, len(result))

        # results are ordered by vote_group index
        self.assertEqual('x', result[0].result)
        self.assertEqual('p', result[1].result)
        self.assertEqual('x', result[2].result)
