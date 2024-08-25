from .validators import TgCommandValidatorMock
from ..primitives import TgUpdatePackage, TgCommand, TgChannel
from .feedback import TelegramReplayGenerator
from ....core import Scenario
from .....infra import Obj
import telegram as tg


def prompt_to_str(v):
    if isinstance(v, TgUpdatePackage):
        return str(v.update)
    return v


def resp_to_str(v):
    if isinstance(v, TgCommand):
        args = ' , '.join([str(z) for z in v.args])
        kwargs = ' , '.join([f"{k} = {v}" for k, v in v.kwargs.items()])
        if args != '' and kwargs!= '':
            sep = ' , '
        else:
            sep = ''

        return f'{v.bot_method} ( {args}{sep}{kwargs} )'
    else:
        return str(v)


def telegram_printing(log, failure):
    return Scenario.default_printing_generic(log, prompt_to_str, resp_to_str, failure)


class TelegramScenario(Scenario):
    CHAT_ID = 1

    def __init__(self, automaton_factory):
        super(TelegramScenario, self).__init__(
            automaton_factory,
            printing=telegram_printing,
            feedback_factory=TelegramReplayGenerator()
        )

    @staticmethod
    def upd(update_type: TgChannel = TgChannel.Text, **dictionary):
        result = Obj()
        dictionary['effective_chat___id'] = TelegramScenario.CHAT_ID
        for key, value in dictionary.items():
            path = key.split('___')
            subobj = result
            for part in path[:-1]:
                if part not in subobj:
                    subobj[part] = Obj()
                subobj = subobj[part]
            subobj[path[-1]] = value
        return TgUpdatePackage(update_type, result)

    @staticmethod
    def val() -> tg.Bot:
        return TgCommandValidatorMock()
