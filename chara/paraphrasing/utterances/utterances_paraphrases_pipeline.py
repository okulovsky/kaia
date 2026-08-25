from avatar.daemon.paraphrase_service import ParaphraseRecord
from .utterance_paraphrase_case_manager import UtteranceParaphraseCaseManager
from ..common import Paraphrase
from .stats_builder import build_statistics, ParaphraseFingerprint, ParaphraseStats
from .selection import ICaseSelection
from .reporting import ParaphraseRunReport, log_statistics
from .uploading import upload
from chara.common import Chara, BatchingPipeline, CaseCollection
from .uterance_paraphrase_case import UtteranceParaphraseCase
from typing import cast


class UtteranceParaphrasePipeline:
    def __init__(self,
                 manager: UtteranceParaphraseCaseManager,
                 settings: Paraphrase.Settings,
                 selection: ICaseSelection,
                 ):
        self.manager = manager
        self.settings = settings
        self.selection = selection

    def __call__(self) -> list[ParaphraseRecord]:
        # Captured before any nested Chara.call() pushes its own subfolder, so the
        # report lands next to this run's result.
        folder = Chara.current.folder

        cases = self.manager.prepare().cases
        cases = cast(CaseCollection[UtteranceParaphraseCase], Paraphrase(cases).prepare()) #Exactly here, otherwise no parsed_template
        cases = CaseCollection(Chara.call(build_statistics)(cases.cases))

        stats_before: dict[ParaphraseFingerprint, ParaphraseStats] = {
            case.stats.fingerprint: case.stats for case in cases.cases
        }
        log_statistics(stats_before.values())
        self.selection.report_plan(stats_before.values())

        pipeline = Paraphrase.Pipeline(self.settings)
        # The selection ends the run by returning nothing. A second stopping condition
        # here would be a run that halts for a reason the caller cannot see.
        batcher = BatchingPipeline[UtteranceParaphraseCase](pipeline, self.selection)
        result = batcher(cases)

        records = self.manager.apply(result.successes)

        # The selection counted what it handed out, including cases that produced nothing.
        report = ParaphraseRunReport.build(stats_before, self.selection.processed, records)
        report.log()
        Chara.call(report.write, 'report')(folder)

        upload(records)
        return records
