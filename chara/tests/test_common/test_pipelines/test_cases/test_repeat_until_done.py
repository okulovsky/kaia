from dataclasses import dataclass, field
from unittest import TestCase
from chara.common.cache import ICache
from chara.common.pipelines.cases import ICase, RepeatUntilDonePipeline, CaseCache
from foundation_kaia.misc import Loc


class SimpleCache(ICache):
    def __init__(self):
        super().__init__(None)


@dataclass
class RetryCase(ICase):
    name: str
    result: int = -1


class InnerPipeline:
    def __init__(self):
        self.attempt = 0

    def __call__(self, cache, cases):
        self.attempt += 1
        for case in cases:
            case.result = self.attempt
            if case.name == 'ok':
                continue
            elif case.name == 'retry' and self.attempt == 1:
                case.error = 'first fail'
                continue
            elif case.name == 'broken':
                case.error = 'always fails'
        cache.write_result(cases)


class RepeatUntilDonePipelineTest(TestCase):
    def test_retry_and_permanent_failure(self):
        # 'ok': succeeds first attempt
        # 'retry': fails once (history empty), then succeeds
        # 'broken': always fails — excluded from results

        cases = [RetryCase('ok'), RetryCase('retry'), RetryCase('broken')]
        with Loc.create_test_folder() as folder:
            cache = CaseCache[RetryCase](folder)
            pipe = RepeatUntilDonePipeline(
                InnerPipeline(),
                attempts=3,
            )
            pipe(cache, cases)
            result = cache.read_result()

        print(result)




