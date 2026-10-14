from chara.common import Chara
from chara.nlu.datasets.text_dataset import TextDatasetPipeline, kaia_intent_templates, MOODS, LANGUAGES
import os
import json

if __name__ == '__main__':
    pipe = TextDatasetPipeline('mistral-small', kaia_intent_templates(), list(LANGUAGES), list(MOODS))
    Chara.start(Chara.Apis.cache_folder / 'nlu/datasets/text-dataset')
    #Chara.invalidate_down('')
    result = Chara.call(pipe)()
    output = Chara.Apis.content_folder / 'nlu/datasets'
    os.makedirs(output, exist_ok=True)
    (output / 'text-dataset.json').write_text(json.dumps(result, indent=2, ensure_ascii=False))
