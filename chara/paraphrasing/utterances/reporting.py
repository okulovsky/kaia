import html
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from avatar.daemon.paraphrase_service import ParaphraseRecord
from chara.common import logger
from .stats_builder import ParaphraseFingerprint, ParaphraseStats

REPORT_FILENAME = 'paraphrase_report.html'
LOGGED_ROWS = 20


def log_statistics(stats: Iterable[ParaphraseStats]) -> None:
    """The whole pool, before anything is selected.

    What a selection makes of this pool is its own to report, so that this module does
    not have to know which behaviours exist.
    """
    stats = list(stats)
    logger.info(
        f"Statistics before the run: {len(stats)} case(s), "
        f"{sum(s.existing for s in stats)} paraphrase(s), {sum(s.seen for s in stats)} play(s)"
    )


@dataclass
class ParaphraseRunRow:
    fingerprint: ParaphraseFingerprint
    seen: int
    existing_before: int
    attempts: int
    produced: int

    @property
    def existing_after(self) -> int:
        return self.existing_before + self.produced

    @property
    def plays_per_paraphrase(self) -> float:
        """The relative deficit DeficitSelection ranks by; above 1.0 means repeats."""
        return self.seen / max(1, self.existing_before)

    @property
    def failed(self) -> bool:
        return self.produced == 0


class ParaphraseRunReport:
    """What this run paraphrased, what the statistics were before it, and what they are now.

    `existing_after` is `existing_before + produced` rather than a re-read of the avatar:
    the run uploads exactly what it produced, so the sum is both exact and cheaper.
    """

    def __init__(self, rows: list[ParaphraseRunRow]):
        self.rows = sorted(rows, key=lambda r: (-r.plays_per_paraphrase, -r.produced))

    @staticmethod
    def build(
            stats_before: dict[ParaphraseFingerprint, ParaphraseStats],
            attempts: dict[ParaphraseFingerprint, int],
            records: Iterable[ParaphraseRecord],
    ) -> 'ParaphraseRunReport':
        produced: dict[ParaphraseFingerprint, int] = {}
        for record in records:
            fingerprint = ParaphraseFingerprint.from_record(record)
            produced[fingerprint] = produced.get(fingerprint, 0) + 1

        rows = []
        for fingerprint in set(attempts) | set(produced):
            stats = stats_before.get(fingerprint, None)
            rows.append(ParaphraseRunRow(
                fingerprint,
                0 if stats is None else stats.seen,
                0 if stats is None else stats.existing,
                attempts.get(fingerprint, 0),
                produced.get(fingerprint, 0),
            ))
        return ParaphraseRunReport(rows)

    @property
    def total_produced(self) -> int:
        return sum(row.produced for row in self.rows)

    @property
    def failures(self) -> list[ParaphraseRunRow]:
        return [row for row in self.rows if row.failed]

    def log(self) -> None:
        logger.info(f"Paraphrased {len(self.rows)} case(s), {self.total_produced} new paraphrase(s)")
        if len(self.failures) > 0:
            logger.info(f"  {len(self.failures)} case(s) produced nothing")
        for row in self.rows[:LOGGED_ROWS]:
            logger.info(
                f"  {row.fingerprint.template_name} "
                f"[{row.fingerprint.language}"
                f"{'' if row.fingerprint.character is None else '/' + row.fingerprint.character}"
                f"{'' if row.fingerprint.record is None else '/' + row.fingerprint.record}] "
                f"seen {row.seen}, {row.plays_per_paraphrase:.2f} play(s) per paraphrase, "
                f"{row.existing_before} -> {row.existing_after} (+{row.produced})"
            )
        if len(self.rows) > LOGGED_ROWS:
            logger.info(f"  ... and {len(self.rows) - LOGGED_ROWS} more, see {REPORT_FILENAME}")

    def write(self, folder: Path) -> Path:
        headers = ('Template', 'Variables', 'Language', 'Character', 'User',
                   'Seen', 'Existing before', 'Plays/paraphrase', 'Attempts', 'Produced', 'Existing after')
        lines = [
            '<html><head><meta charset="utf-8"><style>',
            'body{font-family:sans-serif;font-size:14px}',
            'table{border-collapse:collapse}',
            'th,td{border:1px solid #ccc;padding:4px 8px;text-align:left}',
            'td.n{text-align:right}',
            'tr.failed{background:#fdd}',
            '</style></head><body>',
            f'<h1>Paraphrasing run</h1>',
            f'<p>{len(self.rows)} case(s), {self.total_produced} new paraphrase(s), '
            f'{len(self.failures)} produced nothing.</p>',
            '<table><tr>' + ''.join(f'<th>{h}</th>' for h in headers) + '</tr>',
        ]
        for row in self.rows:
            fingerprint = row.fingerprint
            cells = [
                html.escape(fingerprint.template_name),
                html.escape(fingerprint.variables_tag or ''),
                html.escape(fingerprint.language),
                html.escape(fingerprint.character or ''),
                html.escape(fingerprint.record or ''),
            ]
            numbers = [row.seen, row.existing_before, f'{row.plays_per_paraphrase:.2f}',
                       row.attempts, row.produced, row.existing_after]
            lines.append(
                f'<tr class="{"failed" if row.failed else ""}">'
                + ''.join(f'<td>{c}</td>' for c in cells)
                + ''.join(f'<td class="n">{n}</td>' for n in numbers)
                + '</tr>'
            )
        lines.append('</table></body></html>')

        path = folder / REPORT_FILENAME
        path.write_text('\n'.join(lines), encoding='utf-8')
        return path
