import pickle
from brainbox import BrainBox
from chara.common import CharaApis
from chara.paraphrasing.common.llm_tools import PromptTaskBuilder
from chara.paraphrasing.intents import (
    IntentCaseBuilder, IntentPrompter,
    IntentPipeline, IntentPipelineCache,
)
from kaia.skills.timer_skill import TimerIntents
from kaia.skills.time import TimeIntents
from kaia.skills.date import DateIntents
from foundation_kaia.misc import Loc

all_templates = [
    *TimerIntents.get_templates(),
    *TimeIntents.get_templates(),
    *DateIntents.get_templates(),
]

CharaApis.brainbox_api = BrainBox.Api('127.0.0.1:18090')

cases = IntentCaseBuilder(templates=all_templates, languages=('ru',)).create_cases()

builder = PromptTaskBuilder(prompter=IntentPrompter(), model='mistral')
cache = IntentPipelineCache(Loc.data_folder / 'intent_paraphrases_cache')
IntentPipeline(builder)(cache, cases)

results = cache.read_result()
output = Loc.data_folder / 'intent_paraphrases.pkl'
output.write_bytes(pickle.dumps(results))
print(f"Done. {len(results)} paraphrases → {output}")
