from pathlib import Path
from chara.common import ICache, BrainBoxCache, logger, BrainBoxUnit
from chara.paraphrasing.common.llm_tools import PromptTaskBuilder, BulletPointDivider
from chara.paraphrasing.common.pipeline import ParaphrasePipeline
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
        self.grammar_prompter = grammar_prompter

    def __call__(self, cache: IntentPipelineCache, cases: list[IntentCase],
                 output_path: Path | None = None):
        @logger.phase(cache.llm, "Running LLM")
        def _():
            unit = BrainBoxUnit(self.builder, None, BulletPointDivider())
            unit.run(cache.llm, cases)

        @logger.phase(cache.grammars, "Running Grammars")
        def _():
            if self.grammar_prompter is not None:
                paraphrase_cases = [option for _, option in cache.llm.read_cases_and_options()]
                grammar_builder = PromptTaskBuilder(prompter=self.grammar_prompter, model=self.builder.model)
                unit = BrainBoxUnit(
                    grammar_builder,
                    lambda case, result: self.grammar_prompter.parse_case_response(result)
                )
                unit.run(cache.grammars, paraphrase_cases)
            else:
                cache.grammars.finalize()

        if self.grammar_prompter is not None:
            grammar_map = {case: option for case, option in cache.grammars.read_cases_and_options()}
        else:
            grammar_map = {}

        result = []
        for case, option in cache.llm.read_cases_and_options():
            try:
                grammar_rules = grammar_map.get(option)
                result.append(ParaphrasePipeline.case_and_option_to_record(case, option, grammar_rules))
            except:
                logger.log(f"Option `{option}` failed")

        cache.write_result(result)

        if output_path is not None:
            lines = []
            for record in result:
                lines.append(f"# {record.original_template_name} | {record.language}")
                lines.append(record.filename)
                lines.append("")
            output_path.write_text('\n'.join(lines), encoding='utf-8')
            logger.log(f"{len(result)} paraphrases → {output_path}")
