from brainbox.deciders import Chroma, WD14Tagger
from chara import Chara

def train_tags(tags_model_name: str, wd14_model_name: str|None = None):
    @Chara.phase
    def retrieve_tags():
        return Chara.Apis.brainbox_api.execute(WD14Tagger.new_task().tags(wd14_model_name))

    tags = Chara.previous.result
    tags = [t['name'].replace('_', ' ') for t in tags]

    @Chara.phase
    def train_tags():
        vocab = [dict(text=t) for t in tags]
        Chara.Apis.brainbox_api.execute(Chroma.new_task().train(vocab, tags_model_name))

