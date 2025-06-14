import random
from typing import *
from eaglesong.templates import *
from kaia.kaia import SingleLineKaiaSkill, KaiaContext
from avatar import World, WorldFields
from eaglesong import ContextRequest

CHARACTER_LIST = TemplateVariable(
    'character_list',
    description="List of all the characters available"
)

CHARACTER = TemplateVariable(
    'character',
)

class ChangeCharacterIntents(TemplatesCollection):
    change_character = Template(
        'Change character!',
        f"I want to talk with {CHARACTER}",
    )
    all_characters = Template(
        "What characters are available?"
    )

class ChangeCharacterReplies(TemplatesCollection):
    hello = (
        Template("Hello! Nice to see you!")
        .context(
            f'{World.character} greets {World.user} when seeing {World.user.pronoun} for the first time in the day.',
            reply_to=ChangeCharacterIntents.change_character
        )
    )

    all_characters = (
        Template(f"The characters available are: {CHARACTER_LIST}")
        .context(
            f"{World.user} asks {World.character} about all the characters available in the voice assistant",
            reply_to=ChangeCharacterIntents.all_characters
        )
    )







class ChangeCharacterSkill(SingleLineKaiaSkill):
    def __init__(self,
                 characters_list: Iterable[str]
                 ):
        self.characters_list = tuple(characters_list)
        change_character = ChangeCharacterIntents.change_character.substitute(
            character=OptionsDub(self.characters_list))
        templates = ChangeCharacterIntents.get_templates(change_character)
        super().__init__(templates, ChangeCharacterReplies)


    def run(self):
        input: Utterance = yield
        context: KaiaContext = yield ContextRequest()
        if input in ChangeCharacterIntents.all_characters:
            lst = ', '.join(self.characters_list)
            yield ChangeCharacterReplies.all_characters.utter(character_list=lst)
        if input in ChangeCharacterIntents.change_character:
            value = input.value.get('character', None)
            if value is None:
                yield from context.avatar_api.narration_randomize_character()
            else:
                yield from context.avatar_api.state_change({WorldFields.character: value})












