from pathlib import Path
from chara.common import ICache, BrainBoxCache, logger, BrainBoxUnit
from chara.paraphrasing.common.llm_tools import PromptTaskBuilder, BulletPointDivider
from grammatron import GrammarRule
from .intent_case import IntentCase
from .case_prompter import GrammarPrompter


class IntentPipelineCache(ICache[list]):
    def __init__(self, working_directory: Path | None = None):
        super().__init__(working_directory)
        self.llm = BrainBoxCache[IntentCase, str]()
        self.grammars = BrainBoxCache[str, dict[str, GrammarRule]]()


class IntentPipeline:
    def __init__(self, builder: PromptTaskBuilder, grammar_prompter: GrammarPrompter|None = None):
        self.builder = builder

    def __call__(self, cache: IntentPipelineCache, cases: list[IntentCase]):
        @logger.phase(cache.llm, "Running LLM")
        def _():
            unit = BrainBoxUnit(self.builder, None, BulletPointDivider())
            unit.run(cache.llm, cases)

        @logger.phase(cache.grammars, "Running Grammars")
        def _():
            # If self.grappar_prompter is set, call it here for every paraphrase. If not, just this
            cache.grammars.finalize()
            pass

        result = list(cache.llm.read_cases_and_options())

        # Restore templates with ParaphrasePipeline.case_and_option_to_record.
        # Modify case_and_option_to_record method to pay attention to grammar rules.

        cache.write_result(result)


