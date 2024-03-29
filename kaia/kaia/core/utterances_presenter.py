from kaia.eaglesong.core import Translator, TranslatorInputPackage
from ...avatar.dub.core import Utterance
from .kaia_server import KaiaApi, KaiaMessage

class UtterancesPresenter(Translator):
    def __init__(self, inner_function, kaia_api: KaiaApi):
        self.kaia_api = kaia_api
        super().__init__(
            inner_function,
            None,
            self.report_utterance,
            None,
            None,
            None
        )

    def report_utterance(self, input: TranslatorInputPackage):
        if isinstance(input.outer_input, Utterance):
            self.kaia_api.add_message(KaiaMessage(False, input.outer_input.to_str()))
        return input.outer_input
