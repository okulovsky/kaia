from dataclasses import dataclass
from foundation_kaia.prompters import IPrompter
from avatar.daemon import Character, ParaphraseRecord
from grammatron import Template
from typing import Iterable
from .paraphrase_case import ParaphraseCase
from .jinja_model import JinjaModel
from brainbox.flow import SortedRepresentationStep
from pathlib import Path
from brainbox.flow import Flow
from yo_fluq import FileIO, Query

def rename_with_increment(path: str | Path):
    path = Path(path)
    folder = path.parent
    stem = path.stem        # имя файла без расширения
    suffix = path.suffix    # расширение (с точкой)

    i = 1
    while True:
        new_name = f"{stem}_{i:04d}{suffix}"
        new_path = folder / new_name
        if not new_path.exists():
            path.rename(new_path)
            return new_path
        i += 1

@dataclass
class ParaphraseSetup:
    templates: Iterable[Template]
    users: Iterable[Character]
    characters: Iterable[Character]
    user_to_character_to_relationship: dict[str, dict[str, str]]|None
    relationship: dict[str, IPrompter]|None
    language: str = 'en'

    def _create_cases(self) -> list[ParaphraseCase]:
        result = []
        for user in self.users:
            for character in self.characters:
                if self.user_to_character_to_relationship is not None and self.relationship is not None:
                    relationship = self.relationship[self.user_to_character_to_relationship[user.name][character.name]]
                else:
                    relationship = None
                for template in self.templates:
                    models = JinjaModel.parse_from_template(template)
                    for model in models:
                        result.append(ParaphraseCase(
                            model,
                            character,
                            user,
                            relationship,
                            self.language
                        ))
        return result

    def create_prehistoric_cases(self, records: list[ParaphraseRecord], feedback: dict[str, dict[str,int]]):
        cases = self._create_cases()
        tags_to_case = {case.create_paraphrase_record(None).exact_match_values():case for case in cases}
        for record in records:
            tags = record.exact_match_values()
            if tags in tags_to_case:
                tags_to_case[tags].pre_existing_templates_count += 1
            if record.filename in feedback and 'seen' in feedback[record.filename]:
                tags_to_case[tags].pre_existing_templates_seen += 1
        return list(tags_to_case.values())

    def create_new_cases(self):
        return self._create_cases()

    @staticmethod
    def create_representation_step(count):
        def _item_to_category(item: ParaphraseCase):
            return item.create_paraphrase_record(None).exact_match_values()

        def _item_to_count(item: ParaphraseCase):
            return item.pre_existing_templates_count - item.pre_existing_templates_seen + len(item.result)

        return SortedRepresentationStep(count, _item_to_category, item_to_count=_item_to_count)


    @staticmethod
    def export(path_to_temp_folder: Path, resource_file: Path):
        flow = Flow(path_to_temp_folder)
        records = Query.en(flow.read_flatten()).select_many(lambda z: z.result).to_list()
        if resource_file.is_file():
            data = FileIO.read_pickle(resource_file)
            records = data + records
            rename_with_increment(resource_file)
        FileIO.write_pickle(records, resource_file)

    @staticmethod
    def get_stat_df(path_to_temp_folder: Path):
        flow = Flow(path_to_temp_folder)
        return Query.en(flow.read_flatten()).select_many(lambda z: z.result).select(lambda z: z.__dict__).to_dataframe()


