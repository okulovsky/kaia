from chara.common import Character
from typing import Iterable
from grammatron import Template
from ..common import ParsedTemplate, ParaphraseCase


class CaseBuilder:
    def __init__(self,
                 templates: Iterable[Template],
                 characters: Iterable[Character]|None = None,
                 users: Iterable[Character]|None = None,
                 user_to_character_to_relationship: dict[str, dict[str,str]]|None = None,
                 languages: tuple[str,...] = ('en',)
                 ):
        self.templates = templates
        self.characters = characters
        self.users = None if users is None else tuple(users)
        self.user_to_character_to_relationship = user_to_character_to_relationship
        self.languages = languages

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

    def create_cases(self) -> list[ParaphraseCase]:
        parsed_templates = []
        for template in self._filter_templates(self.templates):
            parsed_templates.extend(ParsedTemplate.parse(template))

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

                for language in self.languages:
                    for parsed_template in parsed_templates:
                        tasks.append(ParaphraseCase(
                            parsed_template,
                            language,
                            character,
                            user,
                            relationship,
                        ))
        return tasks




