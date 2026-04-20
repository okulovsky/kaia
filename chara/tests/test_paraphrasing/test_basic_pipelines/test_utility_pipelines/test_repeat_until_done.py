from dataclasses import dataclass, field
from unittest import TestCase
from chara.common.cache import ICache
from chara.paraphrasing.basic_pipelines.utility_pipelines import (
    UtilityCache, RepeatUntilDonePipeline, CaseStatus,
)
from foundation_kaia.misc import Loc


class SimpleCache(ICache):
    def __init__(self):
        super().__init__(None)


@dataclass
class RetryCase:
    name: str
    status: CaseStatus = CaseStatus.not_started
    error_msg: str | None = None
    history: list = field(default_factory=list)


def inner_pipeline(subcache, cases):
    for case in cases:
        if case.name == 'ok':
            case.status = CaseStatus.success
        elif case.name == 'retry':
            if len(case.history) == 0:
                case.status = CaseStatus.error
                case.error_msg = 'first fail'
            else:
                case.status = CaseStatus.success
                case.error_msg = None
        elif case.name == 'broken':
            case.status = CaseStatus.error
            case.error_msg = 'always fails'
    subcache.write_result(cases)


class RepeatUntilDonePipelineTest(TestCase):
    def test_retry_and_permanent_failure(self):
        # 'ok': succeeds first attempt
        # 'retry': fails once (history empty), then succeeds
        # 'broken': always fails — excluded from results

        cases = [RetryCase('ok'), RetryCase('retry'), RetryCase('broken')]
        with Loc.create_test_folder() as folder:
            cache = UtilityCache(SimpleCache, folder)
            pipe = RepeatUntilDonePipeline(
                inner_pipeline,
                status_field='status',
                error_field='error_msg',
                history_field='history',
                attempts=3,
                raise_if_unsuccessful=False
            )
            pipe(cache, cases)
            result = cache.read_result()
        result_names = [c.name for c in result]

        self.assertIn('ok', result_names)
        self.assertIn('retry', result_names)
        self.assertIn('broken', result_names)

        ok_case = next(c for c in result if c.name == 'ok')
        self.assertEqual(CaseStatus.success, ok_case.status)
        self.assertEqual(1, len(ok_case.history))

        retry_case = next(c for c in result if c.name == 'retry')
        self.assertEqual(CaseStatus.success, retry_case.status)
        self.assertEqual(2, len(retry_case.history))
        self.assertEqual(CaseStatus.error, retry_case.history[0][0])
        self.assertEqual(CaseStatus.success, retry_case.history[1][0])

        broken_case = next(c for c in result if c.name == 'broken')
        self.assertEqual(CaseStatus.error, broken_case.status)
        self.assertEqual(3, len(broken_case.history))
        self.assertEqual(CaseStatus.error, broken_case.history[0][0])
        self.assertEqual(CaseStatus.error, broken_case.history[1][0])



