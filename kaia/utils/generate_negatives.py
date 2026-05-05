from brainbox import BrainBox
from chara.common import CharaApis
from chara.paraphrasing.common.llm_tools import PromptTaskBuilder
from chara.paraphrasing.negatives import (
    NegativeCase, NegativePrompter,
    NegativePipeline, NegativePipelineCache,
)
from foundation_kaia.misc import Loc

MODEL = 'llama3.1:8b'
TARGET = 200
PHRASES_PER_BATCH = 20

CharaApis.brainbox_api = BrainBox.Api('127.0.0.1:8090')

n_batches = max(1, (TARGET + PHRASES_PER_BATCH - 1) // PHRASES_PER_BATCH)
cases = [NegativeCase(language='ru', batch_index=i) for i in range(n_batches)]

builder = PromptTaskBuilder(
    prompter=NegativePrompter(n_phrases=PHRASES_PER_BATCH),
    model=MODEL,
)
cache = NegativePipelineCache(Loc.data_folder / 'negatives_cache')
NegativePipeline(builder)(
    cache, cases,
    output_path=Loc.data_folder / 'negatives.txt',
)
