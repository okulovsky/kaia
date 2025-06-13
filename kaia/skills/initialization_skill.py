from ..kaia import IKaiaSkill, InitializationCommand, KaiaContext
from eaglesong import ContextRequest


class InitializationSkill(IKaiaSkill):
    def __init__(self, state_fields: dict|None = None):
        self.state_fields = state_fields if state_fields is not None else {}

    def get_name(self) -> str:
        return type(self).__name__

    def should_start(self, input) -> bool:
        return isinstance(input, InitializationCommand)

    def get_type(self) -> 'IKaiaSkill.Type':
        return IKaiaSkill.Type.SingleLine

    def should_proceed(self, input) -> bool:
        return False

    def get_runner(self):
        return self.run

    def run(self):
        context: KaiaContext = yield ContextRequest()
        yield from context.avatar_api.narration_reset()












