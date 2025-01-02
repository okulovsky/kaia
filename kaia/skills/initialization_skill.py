from ..kaia import IKaiaSkill, Start
from .character_skill import ChangeCharacterSkill

class InitializationSkill(IKaiaSkill):
    def __init__(self,
                 character_skill: ChangeCharacterSkill
                 ):
        self.character_skill = character_skill

    def get_name(self) -> str:
        return type(self).__name__

    def should_start(self, input) -> bool:
        return isinstance(input, Start)

    def get_type(self) -> 'IKaiaSkill.Type':
        return IKaiaSkill.Type.SingleLine

    def should_proceed(self, input) -> bool:
        return False

    def get_runner(self):
        return self.run

    def run(self):
        yield from self.character_skill.switch_to_character()





