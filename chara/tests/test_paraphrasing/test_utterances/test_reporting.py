import unittest

from avatar.daemon.paraphrase_service import ParaphraseRecord
from foundation_kaia.misc import Loc

from chara.paraphrasing.utterances import ParaphraseRunReport
from chara.paraphrasing.utterances.reporting import REPORT_FILENAME
from chara.paraphrasing.utterances.stats_builder import ParaphraseFingerprint, ParaphraseStats


def fingerprint(name: str) -> ParaphraseFingerprint:
    return ParaphraseFingerprint(name, 'tag', 'en', 'Alice', 'Bob')


def record(name: str) -> ParaphraseRecord:
    return ParaphraseRecord('file', None, name, 'tag', 'en', 'Alice', 'Bob')


def stats(name: str, existing: int, seen: int) -> ParaphraseStats:
    return ParaphraseStats(fingerprint(name), existing, seen)


class ParaphraseRunReportTestCase(unittest.TestCase):
    def _report(self) -> ParaphraseRunReport:
        before = {fingerprint('hello'): stats('hello', 4, 12), fingerprint('bye'): stats('bye', 1, 3)}
        attempts = {fingerprint('hello'): 1, fingerprint('bye'): 2}
        records = [record('hello')] * 3
        return ParaphraseRunReport.build(before, attempts, records)

    def test_before_and_after(self):
        row = self._report().rows[0]
        self.assertEqual('hello', row.fingerprint.template_name)
        self.assertEqual(12, row.seen)
        self.assertEqual(4, row.existing_before)
        self.assertEqual(3, row.produced)
        self.assertEqual(7, row.existing_after)

    def test_an_attempt_that_produced_nothing_is_still_reported(self):
        failures = self._report().failures
        self.assertEqual(['bye'], [row.fingerprint.template_name for row in failures])
        self.assertEqual(2, failures[0].attempts)
        self.assertEqual(1, failures[0].existing_after, "nothing produced, so nothing changed")

    def test_rows_are_ordered_by_relative_deficit(self):
        # hello: 12 seen against 4 existing, 3.0 plays each; bye: 3 against 1, 3.0 - tie,
        # broken by what was produced.
        self.assertEqual(['hello', 'bye'], [row.fingerprint.template_name for row in self._report().rows])

    def test_plays_per_paraphrase(self):
        self.assertEqual(3.0, self._report().rows[0].plays_per_paraphrase)

    def test_totals(self):
        report = self._report()
        self.assertEqual(3, report.total_produced)
        self.assertEqual(2, len(report.rows))

    def test_a_fingerprint_with_no_prior_statistics_starts_at_zero(self):
        report = ParaphraseRunReport.build({}, {}, [record('new')])
        self.assertEqual(0, report.rows[0].existing_before)
        self.assertEqual(1, report.rows[0].existing_after)

    def test_written_report_holds_the_numbers(self):
        with Loc.create_test_folder() as folder:
            path = self._report().write(folder)
            self.assertEqual(folder/REPORT_FILENAME, path)
            html = path.read_text(encoding='utf-8')
        self.assertIn('hello', html)
        self.assertIn('3 new paraphrase(s)', html)
        self.assertIn('<td class="n">7</td>', html)
        self.assertIn('<td class="n">3.00</td>', html)
        self.assertIn('class="failed"', html)


if __name__ == '__main__':
    unittest.main()
