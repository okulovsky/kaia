from chara import CaseCollection, BrainBoxCasePipeline, Chara
from brainbox.deciders import Chroma

class TagMatchingPipeline:
    def __init__(self,
                 collection_name: str,
                 text_field: str,
                 tags_field: str,
                 tags_per_input: int = 30
                 ):
        self.collection_name = collection_name
        self.tags_per_input = tags_per_input
        self.text_field = text_field
        self.tags_field = tags_field


    def _create_task(self, case):
        return Chroma.new_task().find_neighbors(getattr(case, self.text_field), self.tags_per_input, self.collection_name)

    def _apply(self, case, result):
        tags = tuple(r['text'] for r in result)
        setattr(case, self.tags_field, tags)

    def __call__(self, cases: CaseCollection) -> CaseCollection:
        pipe = BrainBoxCasePipeline(self._create_task, self._apply)
        return Chara.call(pipe)(cases)