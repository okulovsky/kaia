import random
from typing import *
from kaia.avatar.dub.languages.en import *
from kaia.kaia.core import SingleLineKaiaSkill
from kaia.avatar.server import AvatarAPI

class ChangeCharacterReplies(TemplatesCollection):
    hello = Template(
        "Hello! Nice to see you!"
    )
    all_characters = Template(
        "The characters available are: {character_list}",
        character_list = IdentityDub()
    )


class ChangeCharacterIntents(TemplatesCollection):
    change_character = Template(
        'Change character!',
        "I want to talk with {character}",
        character = Dub()
    )
    all_characters = Template(
        "What characters are available?"
    )

class ChangeCharacterSkill(SingleLineKaiaSkill):
    def __init__(self,
                 characters_list: Iterable[str],
                 avatar_api: AvatarAPI,
                 character_field_name: str = 'character',
                 dont_randomly_switch_to: Optional[Iterable[str]] = None
                 ):
        self.avatar_api = avatar_api
        self.character_field_name = character_field_name
        self.characters_list = tuple(characters_list)
        self.dont_randomly_switch_to = list(dont_randomly_switch_to) if dont_randomly_switch_to is not None else []
        substitution = dict(character = StringSetDub(self.characters_list))
        self.intents: Type[ChangeCharacterIntents] = ChangeCharacterIntents.substitute(substitution)
        super().__init__(self.intents, ChangeCharacterReplies)

    def run(self):
        input: Utterance = yield
        if input.template.name == ChangeCharacterIntents.all_characters.name:
            lst = ', '.join(self.characters_list)
            yield ChangeCharacterReplies.all_characters.utter(character_list=lst)
        if input.template.name == ChangeCharacterIntents.change_character.name:
            value = input.value.get('character', None)
            if value is None:
                current_state = self.avatar_api.state_get()
                current_character = current_state[self.character_field_name]
                other_characters = [c for c in self.characters_list if c != current_character and c not in self.dont_randomly_switch_to]
                if len(other_characters) == 0:
                    return
                value = other_characters[random.randint(0, len(other_characters)-1)]

            self.avatar_api.state_change({self.character_field_name:value})
            yield self.avatar_api.image_get()
            yield ChangeCharacterReplies.hello.utter()








