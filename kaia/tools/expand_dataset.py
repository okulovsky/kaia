from pathlib import Path
from chara.paraphrasing.expand import ExpandPipeline, ExpandPipelineCache
from foundation_kaia.misc import Loc
from yo_fluq import FileIO

records = FileIO.read_pickle(Loc.data_folder / 'result')

cache = ExpandPipelineCache(Loc.data_folder / 'expand_cache')
ExpandPipeline(n_values=5, language='ru')(
    cache, records,
    output_path=Loc.data_folder / 'intent_paraphrases_expanded.txt',
)
