from kaia.app import AssistantFactory
from chara.common import Chara
from chara.nlu.datasets.text_dataset import TextDatasetPipeline
import os
import json

if __name__ == '__main__':
    factory = AssistantFactory(None)
    assistant = factory.create_assistant(None)
    intents_packs = assistant.get_intents()
    templates = []
    for pack in intents_packs:
        templates.extend(pack.templates)
    moods = [
        'User speaks neutrally and clearly',
        'User speaks quickly and briefly, no filler words',
        "User is angry because of the previous unsuccessful attempts, speaks accordingly",
        "User is in a good mood and speaks with assistant as if it was a real person",
    ]
    languages = ['en', 'de', 'ru']
    pipe = TextDatasetPipeline('mistral-small', templates, languages, moods)
    Chara.start(Chara.Apis.cache_folder / 'nlu/datasets/text-dataset')
    #Chara.invalidate_down('')
    result = Chara.call(pipe)()
    output = Chara.Apis.content_folder / 'nlu/datasets'
    os.makedirs(output, exist_ok=True)
    (output / 'text-dataset.json').write_text(json.dumps(result, indent=2, ensure_ascii=False))
