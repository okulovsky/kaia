from brainbox.flow import IStep, BulletPointParser
from typing import cast
from .paraphrase_case import ParaphraseCase
import traceback

class LLMParsingStep(IStep):
    def process(self, history, current):
        parser = BulletPointParser()
        for item in current:
            templates = []
            try:
                for s in parser(item.answer):
                    try:
                        templates.append(item.create_paraphrase_record(s))
                    except:
                        print(f"Parsing failed at `{s}`, template `{item.model.template.sequence}`")
                        print(traceback.format_exc())
            except:
                pass
            item = cast(ParaphraseCase, item)
            item.result = tuple(templates)
        return current




