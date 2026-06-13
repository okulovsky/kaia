from chara.common import Chara
from .uterance_paraphrase_case import UtteranceParaphraseCase
from avatar.daemon.paraphrase_service import ParaphraseRecord, ParaphraseService
import json
import pickle
from dataclasses import dataclass

@dataclass(frozen=True)
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
    fingerprint: ParaphraseFingerprint
    existing: int = 0
    seen: int = 0




def _read_existing() -> list[ParaphraseRecord]:
    existing = []
    rs = Chara.Apis.avatar_api.resources(ParaphraseService)
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
    rs = Chara.Apis.avatar_api.resources(ParaphraseService)
    if not rs.is_file(ParaphraseService.FEEDBACK_FILENAME):
        return {}
    return json.loads(rs.read('paraphrases-feedback.json'))


def _create_statistics(cases: tuple[UtteranceParaphraseCase,...]) -> dict[ParaphraseFingerprint, ParaphraseStats]:
    fp_to_stat = {}
    for case in cases:
        fp = ParaphraseFingerprint.from_case(case)
        if fp in fp_to_stat:
            raise ValueError(
                f"Paraphrase-to-fingrprint must describe only one paraphrase\n{fp}")
        case.stats = ParaphraseStats(fp)
        fp_to_stat[fp] = case.stats

    return fp_to_stat


def _fill_statistics(
        fp_to_stat: dict[ParaphraseFingerprint, ParaphraseStats]):
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


def build_statistics(tasks: tuple[UtteranceParaphraseCase,...]):
    stats = _create_statistics(tasks)
    _fill_statistics(stats)
    return tasks







