import random
from typing import *
from kaia.dub.languages.en import *
from kaia.kaia import SingleLineKaiaSkill, KaiaContext
from kaia.avatar import World, KnownFields
from eaglesong import ContextRequest


class ChangeCharacterReplies(TemplatesCollection):
    hello = (
        Template("Hello! Nice to see you!")
        .paraphrase(f'{World.character} comes to the room and sees {World.user} for the first time today.')
    )

    all_characters = Template(
        "The characters available are: {character_list}",
        character_list = ToStrDub()
    )




class ChangeCharacterIntents(TemplatesCollection):
    change_character = Template(
        'Change character!',
        "I want to talk with {character}",
        character = ToStrDub()
    )
    all_characters = Template(
        "What characters are available?"
    )


class ChangeCharacterSkill(SingleLineKaiaSkill):
    def __init__(self,
                 characters_list: Iterable[str]
                 ):
        self.characters_list = tuple(characters_list)
        substitution = dict(character = StringSetDub(self.characters_list))
        self.intents: Type[ChangeCharacterIntents] = ChangeCharacterIntents.substitute(substitution)
        super().__init__(self.intents, ChangeCharacterReplies)


    def run(self):
        input: Utterance = yield
        context: KaiaContext = yield ContextRequest()
        if input.template.name == ChangeCharacterIntents.all_characters.name:
            lst = ', '.join(self.characters_list)
            yield ChangeCharacterReplies.all_characters.utter(character_list=lst)
        if input.template.name == ChangeCharacterIntents.change_character.name:
            value = input.value.get('character', None)
            if value is None:
                yield from context.avatar_api.narration_randomize_character()
            else:
                yield from context.avatar_api.state_change({KnownFields.character: value})












