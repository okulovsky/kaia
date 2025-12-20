from chara.common import ICache, BrainBoxCache, logger, BrainBoxUnit
from pathlib import Path
from .paraphrase_case import ParaphraseCase
from .llm_tools import BulletPointDivider, PromptTaskBuilder
from avatar.daemon import ParaphraseRecord


class ParaphraseCache(ICache[list[ParaphraseRecord]]):
    def __init__(self, working_directory: Path|None = None):
        super().__init__(working_directory)
        self.llm = BrainBoxCache[ParaphraseCase, str]()


class ParaphrasePipeline:
    def __init__(self, builder: PromptTaskBuilder):
        self.builder = builder

    def __call__(self, cache: ParaphraseCache, cases: list[ParaphraseCase]):
        @logger.phase(cache.llm, "Running LLM")
        def _():
            unit = BrainBoxUnit(
                self.builder,
                None, #We could restore templates here, but it's more convenient for logging to do it after
                BulletPointDivider(),
            )
            unit.run(cache.llm, cases)

        result = []
        for case, option in cache.llm.read_cases_and_options():
            result.append(ParaphrasePipeline.case_and_option_to_record(case, option))

        cache.write_result(result)

    @staticmethod
    def case_and_option_to_record(case: ParaphraseCase, option: str):
        template = case.template.restore_template(option)
        return ParaphraseRecord(
            option,
            template,
            case.template.template.get_name(),
            case.template.variables_tag,
            case.language,
            None if case.character is None else case.character.name,
            None if case.user is None else case.user.name
        )



