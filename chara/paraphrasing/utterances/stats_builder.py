from ...common import CharaApis
from .uterance_paraphrase_case import UtteranceParaphraseCase
from avatar.daemon.paraphrase_service import ParaphraseRecord, ParaphraseService
import json
import pickle
from dataclasses import dataclass

@dataclass
class ParaphraseFingerprint:
    template_name: str
    variables_tag: str
    language: str
    character: str|None
    record: str|None

    @staticmethod
    def from_record(record: ParaphraseRecord) -> 'ParaphraseFingerprint':
        return ParaphraseFingerprint(
            record.original_template_name,
            record.used_variables_tag,
            record.language,
            record.character,
            record.user
        )

    @staticmethod
    def from_case(case: UtteranceParaphraseCase) -> 'ParaphraseFingerprint':
        return ParaphraseFingerprint(
            case.original_template.get_name(),
            case.parsed_template.variables_tag,
            case.target_language_code,
            None if case.character is None else case.character.name,
            None if case.user is None else case.user.name
        )


@dataclass
class ParaphraseStats:
    case: UtteranceParaphraseCase
    fingerprint: ParaphraseFingerprint
    existing: int = 0
    seen: int = 0

    @property
    def availability(self) -> int:
        return self.existing - self.seen



def _read_existing() -> list[ParaphraseRecord]:
    existing = []
    rs = CharaApis.avatar_api.resources(ParaphraseService)
    files = rs.list(
        '/',
        prefix=ParaphraseService.PARAPHRASES_PREFIX,
        suffix=ParaphraseService.PARAPHRASES_SUFFIX
    )
    if files is None:
        files = []
    for file in files:
        existing.extend(pickle.loads(rs.read(file)))
    return existing


def _read_feedback() -> dict[str, dict[str, int]]:
    rs = CharaApis.avatar_api.resources(ParaphraseService)
    if not rs.is_file(ParaphraseService.FEEDBACK_FILENAME):
        return {}
    return json.loads(rs.read('paraphrases-feedback.json'))


def _create_statistics(tasks: list[UtteranceParaphraseCase]) -> dict[ParaphraseFingerprint, ParaphraseStats]:
    fp_to_task = {}
    for index, task in enumerate(tasks):
        fp = ParaphraseFingerprint.from_case(task)
        if fp in fp_to_task:
            raise ValueError(
                f"Paraphrase-to-fingrprint must describe only one paraphrase\n{fp}\n{index}, {fp_to_task[fp][0]}")
        fp_to_task[fp] = (index, task)

    fp_to_stat = {key: ParaphraseStats(value[1], key) for key, value in fp_to_task.items()}
    return fp_to_stat


def _fill_statistics(
        fp_to_stat: dict[ParaphraseFingerprint, ParaphraseStats]) -> list[ParaphraseStats]:
    name_to_fp = {}

    for record in _read_existing():
        fp = ParaphraseFingerprint.from_record(record)
        name_to_fp[record.filename] = fp
        if fp not in fp_to_stat:
            continue
        fp_to_stat[fp].existing += 1

    for name, fb in _read_feedback().items():
        if name not in name_to_fp:
            continue
        fp = name_to_fp[name]
        if fp not in fp_to_stat:
            continue
        if 'seen' not in fb:
            continue
        fp_to_stat[fp].seen += fb['seen']

    stats = list(fp_to_stat.values())
    return stats

def build_statistics(tasks: list[UtteranceParaphraseCase]) -> list[ParaphraseStats]:
    stats = _create_statistics(tasks)
    stats = _fill_statistics(stats)
    return stats


def add_prior_result(stats: list[ParaphraseStats],
                     prior_result: list[ParaphraseRecord]) -> None:
    fp_to_stat = {s.fingerprint:s for s in stats}
    for record in prior_result:
        fp = ParaphraseFingerprint.from_record(record)
        if fp not in fp_to_stat:
            continue
        fp_to_stat[fp].existing += 1


def sort_statistics(stats: list[ParaphraseStats], only_completely_missing: bool) -> list[ParaphraseStats]:
    if only_completely_missing:
        stats = [s for s in stats if s.existing == 0]
    return list(sorted(stats, key=lambda z: z.availability))






