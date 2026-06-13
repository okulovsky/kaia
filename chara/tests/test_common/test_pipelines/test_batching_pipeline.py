from dataclasses import dataclass
from unittest import TestCase
from foundation_kaia.misc import Loc
from chara.common import Chara, BatchingPipeline, ICase, CaseCollection, CaseRepetition


@dataclass
class BatchCase(ICase):
    name: str
    result: int = -1


def selector_pending(summaries: list[CaseRepetition.Summary[BatchCase]]) -> list[BatchCase]:
    return [s.case for s in summaries if len(s.successes) == 0]


class BatchingPipelineTest(TestCase):
    def test_all_succeed(self):
        class InnerPipeline:
            def __call__(self, cases: CaseCollection[BatchCase]) -> CaseCollection[BatchCase]:
                for case in cases.cases:
                    case.result = 1
                return cases

        cases = CaseCollection([BatchCase('a'), BatchCase('b'), BatchCase('c')])
        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            pipe = BatchingPipeline(InnerPipeline(), selector_pending)
            result = Chara.call(pipe.__call__)(cases)

        self.assertEqual(3, len(result.cases))
        self.assertTrue(all(c.result == 1 for c in result.cases))

    def test_partial_retry(self):
        # 'flaky' fails on attempt 1, succeeds on attempt 2
        class InnerPipeline:
            def __init__(self):
                self.attempt = 0

            def __call__(self, cases: CaseCollection[BatchCase]) -> CaseCollection[BatchCase]:
                self.attempt += 1
                for case in cases.cases:
                    case.result = self.attempt
                    if case.name == 'flaky' and self.attempt == 1:
                        case.error = 'first fail'
                return cases

        cases = CaseCollection([BatchCase('ok'), BatchCase('flaky')])
        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            pipe = BatchingPipeline(InnerPipeline(), selector_pending)
            result = Chara.call(pipe.__call__)(cases)

        self.assertEqual(2, len(result.cases))
        ok = next(c for c in result.cases if c.name == 'ok')
        self.assertEqual(1, ok.result)
        flaky = next(c for c in result.cases if c.name == 'flaky')
        self.assertEqual(2, flaky.result)

    def test_max_batch_iterations(self):
        # All cases always fail; loop must stop at max_batch_iterations
        class InnerPipeline:
            def __init__(self):
                self.attempt = 0

            def __call__(self, cases: CaseCollection[BatchCase]) -> CaseCollection[BatchCase]:
                self.attempt += 1
                for case in cases.cases:
                    case.error = f'fail {self.attempt}'
                return cases

        inner = InnerPipeline()
        cases = CaseCollection([BatchCase('a'), BatchCase('b')])
        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            pipe = BatchingPipeline(inner, selector_pending, max_batch_iterations=3)
            result = Chara.call(pipe.__call__)(cases)

        self.assertEqual(3, inner.attempt)
        self.assertEqual(0, len(result.cases))

    def test_dropped_case_counted_as_error(self):
        # Pipeline drops 'fragile' (doesn't return it at all)
        # Selector only retries cases with no errors — so after the drop, 'fragile' is excluded
        # Without dropped-case tracking, 'fragile' would be retried up to max_batch_iterations times
        class InnerPipeline:
            def __init__(self):
                self.attempt = 0

            def __call__(self, cases: CaseCollection[BatchCase]) -> CaseCollection[BatchCase]:
                self.attempt += 1
                kept = []
                for case in cases.cases:
                    if case.name == 'fragile':
                        pass  # drop it — don't include in result
                    else:
                        case.result = self.attempt
                        kept.append(case)
                return CaseCollection(kept)

        def selector_no_errors(summaries):
            return [s.case for s in summaries if len(s.successes) == 0 and len(s.errors) == 0]

        inner = InnerPipeline()
        cases = CaseCollection([BatchCase('ok'), BatchCase('fragile')])
        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            pipe = BatchingPipeline(inner, selector_no_errors, max_batch_iterations=5)
            result = Chara.call(pipe.__call__)(cases)

        # 'fragile' was dropped on iteration 1 → gets error "Dropped" → excluded from further batches
        # So the pipeline is called only once (not up to 5 times for 'fragile')
        self.assertEqual(1, inner.attempt)
        self.assertEqual(1, len(result.cases))
        self.assertEqual('ok', result.cases[0].name)
