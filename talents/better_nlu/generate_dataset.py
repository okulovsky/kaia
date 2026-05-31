from chara.nlu.dataset import DatasetGenerationCache, DatasetGenerationPipeline, export_dataset
from foundation_kaia.misc import Loc
from kaia.app import AssistantFactory
from pprint import pprint
import pickle

if __name__ == "__main__":
    cache = DatasetGenerationCache(Loc.data_folder/'nlu-dataset')
    #cache.delete()
    pipe = DatasetGenerationPipeline(
        'mistral-small',
        [
            'User speaks neutrally and clearly',
            'User speaks quickly and briefly, no filler words',
            "User is angry because of the previous unsuccessful attempts, speaks accordingly",
            "User is in a good mood and speaks with assistant as if it was a real person",
        ],
        [
            'ru', 'de', 'en'
        ]
    )
    assistant = AssistantFactory(None).create_assistant(None)
    intents = assistant.get_intents()
    templates = next(i for i in intents if i.name=='CORE').templates
    allowed_intents = (
        'kaia.skills.time.TimeIntents.question', #No variables
        'kaia.skills.cookbook_skill.intents.CookBookIntents.recipe', #with OptionsDub
        'kaia.skills.timer_skill.TimerIntents.set_the_timer' # with TimedeltaDub
    )
    #templates = [t for t in templates if t.get_name() in allowed_intents]
    pipe(cache, templates)

    result = export_dataset(cache.read_result())
    with open(Loc.data_folder/'nlu-dataset.pkl', 'wb') as file:
        pickle.dump(result, file)
    for item in result:
        pprint(item)


