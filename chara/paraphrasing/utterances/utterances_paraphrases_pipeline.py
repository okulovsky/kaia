from avatar.daemon.paraphrase_service import ParaphraseRecord
from .utterance_paraphrase_case_manager import UtteranceParaphraseCaseManager
from ..common import Paraphrase
from .stats_builder import build_statistics, ParaphraseFingerprint, ParaphraseStats
from .prioritization import ParaphrasePrioritization
from .reporting import ParaphraseRunReport, log_statistics
from .uploading import upload
from chara.common import Chara, CaseCollection
from .uterance_paraphrase_case import UtteranceParaphraseCase
from typing import cast


class UtteranceParaphrasePipeline:
    def __init__(self,
                 manager: UtteranceParaphraseCaseManager,
                 settings: Paraphrase.Settings,
                 prioritization: ParaphrasePrioritization,
                 ):
        self.manager = manager
        self.settings = settings
        self.prioritization = prioritization

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

        selected = Chara.call(self.prioritization, 'prioritization')(cases)
        result = Chara.call(Paraphrase.Pipeline(self.settings), 'paraphrase')(selected.successes_collection)

        records = self.manager.apply(result.successes)

        # Includes the selected cases that produced nothing
        processed = {case.stats.fingerprint for case in selected.successes}
        report = ParaphraseRunReport.build(stats_before, processed, records)
        report.log()
        Chara.call(report.write, 'report')(folder)

        upload(records)
        return records
