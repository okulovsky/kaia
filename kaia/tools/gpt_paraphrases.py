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

all_templates = [
    *TimerIntents.get_templates(),
    *TimeIntents.get_templates(),
    *DateIntents.get_templates(),
]

CharaApis.brainbox_api = BrainBox.Api('127.0.0.1:8090')

cases = IntentCaseBuilder(templates=all_templates, languages=('ru',)).create_cases()

builder = PromptTaskBuilder(prompter=IntentPrompter(), model=MODEL)
cache = IntentPipelineCache(Loc.data_folder / 'intent_paraphrases_cache')
IntentPipeline(builder, grammar_prompter=RuGrammarPrompter())(cache, cases)

results = cache.read_result()
output = Loc.data_folder / 'intent_paraphrases.txt'
lines = []
for record in results:
    lines.append(f"# {record.original_template_name} | {record.language}")
    lines.append(record.filename)
    lines.append("")
output.write_text('\n'.join(lines), encoding='utf-8')
print(f"Done. {len(results)} paraphrases → {output}")
