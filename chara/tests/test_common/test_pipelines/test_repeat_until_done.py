from dataclasses import dataclass
from unittest import TestCase
from foundation_kaia.misc import Loc
from chara.common import Chara, RepeatUntilDonePipeline, ICase, CaseCollection


@dataclass
class RetryCase(ICase):
    name: str
    result: int = -1


class InnerPipeline:
    def __init__(self):
        self.attempt = 0

    def __call__(self, cases: CaseCollection[RetryCase]) -> CaseCollection[RetryCase]:
        self.attempt += 1
        for case in cases.cases:
            case.result = self.attempt
            if case.name == 'ok':
                pass
            elif case.name == 'retry' and self.attempt == 1:
                case.error = 'first fail'
            elif case.name == 'broken':
                case.error = 'always fails'
        return cases


class RepeatUntilDonePipelineTest(TestCase):
    def test_retry_and_permanent_failure(self):
        # 'ok': succeeds first attempt
        # 'retry': fails once, then succeeds on attempt 2
        # 'broken': always fails — gets error message
        cases = CaseCollection([RetryCase('ok'), RetryCase('retry'), RetryCase('broken')])
        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            pipe = RepeatUntilDonePipeline(InnerPipeline(), attempts=3)
            result = Chara.call(pipe.__call__)(cases)

        all_cases = result.cases
        self.assertEqual(3, len(all_cases))

        ok = next(c for c in all_cases if c.name == 'ok')
        self.assertIsNone(ok.error)
        self.assertEqual(1, ok.result)

        retry = next(c for c in all_cases if c.name == 'retry')
        self.assertIsNone(retry.error)
        self.assertEqual(2, retry.result)

        broken = next(c for c in all_cases if c.name == 'broken')
        self.assertIsNotNone(broken.error)
