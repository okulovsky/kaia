from chara.common import Character
from typing import Iterable
from grammatron import Template
from .uterance_paraphrase_case import UtteranceParaphraseCase
from avatar.daemon.paraphrase_service import ParaphraseRecord
from uuid import uuid4


class UtteranceParaphraseCaseManager:
    def __init__(self,
                 templates: Iterable[Template],
                 characters: Iterable[Character]|None = None,
                 users: Iterable[Character]|None = None,
                 user_to_character_to_relationship: dict[str, dict[str,str]]|None = None,
                 target_languages: tuple[str,...] = ('en',)
                 ):
        self.templates = templates
        self.characters = characters
        self.users = None if users is None else tuple(users)
        self.user_to_character_to_relationship = user_to_character_to_relationship
        self.target_languages = target_languages

    def _filter_templates(self, all_templates: Iterable[Template]) -> list[Template]:
        names = set()
        filtered_templates = []
        for template in all_templates:
            name = template.get_name()
            if name in names:
                continue
            names.add(name)
            filtered_templates.append(template)
        return filtered_templates

    def prepare(self) -> list[UtteranceParaphraseCase]:
        tasks = []
        users = [None] if self.users is None else self.users
        characters = [None] if self.characters is None else self.characters
        for character in characters:
            for user in users:
                if self.user_to_character_to_relationship is None:
                    relationship = None
                elif user is None or character is None:
                    relationship = None
                else:
                    relationship = self.user_to_character_to_relationship.get(user.name, {}).get(character.name, None)

                for language in self.target_languages:
                    for template in self._filter_templates(self.templates):
                        tasks.append(UtteranceParaphraseCase(
                            template,
                            language,
                            character,
                            user,
                            relationship,
                        ))
        return tasks


    def apply(self, cases: list[UtteranceParaphraseCase]) -> list[ParaphraseRecord]:
        result = []
        for case in cases:
            result.append(ParaphraseRecord(
                str(uuid4()),
                case.resulting_template,
                case.original_template.get_name(),
                case.parsed_template.variables_tag,
                case.target_language_code,
                None if case.character is None else case.character.name,
                None if case.user is None else case.user.name
            ))
        return result



