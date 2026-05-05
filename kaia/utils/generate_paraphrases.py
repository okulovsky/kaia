from brainbox import BrainBox
from chara.common import CharaApis
from chara.paraphrasing.common.llm_tools import PromptTaskBuilder
from chara.paraphrasing.intents import (
    IntentCaseBuilder, IntentPrompter,
    IntentPipeline, IntentPipelineCache,
    RuGrammarPrompter,
)
from kaia.skills.timer_skill import TimerIntents
from kaia.skills.time import TimeIntents
from kaia.skills.date import DateIntents
from foundation_kaia.misc import Loc

MODEL = 'llama3.1:8b'

CharaApis.brainbox_api = BrainBox.Api('127.0.0.1:8090')

all_templates = [
    *TimerIntents.get_templates(),
    *TimeIntents.get_templates(),
    *DateIntents.get_templates(),
]

cases = IntentCaseBuilder(templates=all_templates, languages=('ru',)).create_cases()
builder = PromptTaskBuilder(prompter=IntentPrompter(), model=MODEL)
cache = IntentPipelineCache(Loc.data_folder / 'intent_paraphrases_cache')
IntentPipeline(builder, grammar_prompter=RuGrammarPrompter())(
    cache, cases,
    output_path=Loc.data_folder / 'intent_paraphrases.txt',
)
