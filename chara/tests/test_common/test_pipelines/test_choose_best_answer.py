from unittest import TestCase
from foundation_kaia.misc import Loc
from chara.common import Chara, ChooseBestAnswerPipeline, CaseCollection, IVotingCase


class VotingCase(IVotingCase):
    def __init__(self, name: str):
        self.name = name
        self.result: str | None = None

    def get_result_fingerprint(self) -> str:
        return self.result


class Pipeline:
    def __init__(self, results_per_round):
        self.call_count = 0
        self.results_per_round = results_per_round

    def __call__(self, cases: CaseCollection[VotingCase]) -> CaseCollection[VotingCase]:
        i = self.call_count
        self.call_count += 1
        for case in cases.cases:
            case.result = self.results_per_round[i][case.name]
        return cases


class ChooseBestAnswerPipelineTest(TestCase):
    def test_majority_vote(self):
        # case 'a': rounds produce 'x', 'x', 'y'  → winner 'x'
        # case 'b': rounds produce 'p', 'q', 'p'  → winner 'p'
        # case 'c': rounds produce 'x', 'y', 'z'  → winner 'x' (tied, alphabetical)
        inner_pipe = Pipeline([
            {'a': 'x', 'b': 'p', 'c': 'x'},
            {'a': 'x', 'b': 'q', 'c': 'y'},
            {'a': 'y', 'b': 'p', 'c': 'z'},
        ])

        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            pipe = ChooseBestAnswerPipeline(inner_pipe, poll_size=3)
            result = Chara.call(pipe.__call__)(CaseCollection([VotingCase('a'), VotingCase('b'), VotingCase('c')]))

        cases = result.cases
        self.assertEqual(3, len(cases))
        self.assertEqual('x', cases[0].result)
        self.assertEqual('p', cases[1].result)
        self.assertEqual('x', cases[2].result)
