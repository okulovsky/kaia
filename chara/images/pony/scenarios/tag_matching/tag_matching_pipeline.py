from chara import CaseCollection, BrainBoxCasePipeline, Chara
from brainbox.deciders import Chroma

class TagMatchingPipeline:
    def __init__(self,
                 case_to_collection_name,
                 case_to_text,
                 case_to_tag_count,
                 tags_field: str,
                 ):
        self.case_to_collection_name = case_to_collection_name
        self.case_to_text = case_to_text
        self.tags_field = tags_field
        self.case_to_tag_count = case_to_tag_count


    def _create_task(self, case):
        return Chroma.new_task().find_neighbors(self.case_to_text(case), self.case_to_tag_count(case), self.case_to_collection_name(case))

    def _apply(self, case, result):
        tags = tuple(r['text'] for r in result)
        setattr(case, self.tags_field, tags)

    def __call__(self, cases: CaseCollection) -> CaseCollection:
        pipe = BrainBoxCasePipeline(self._create_task, self._apply)
        return Chara.call(pipe)(cases)