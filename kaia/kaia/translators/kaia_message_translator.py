from typing import *
from kaia.eaglesong.core import Translator, TranslatorInputPackage, Empty
from kaia.dub.core import Utterance
from kaia.kaia.gui import KaiaGuiApi, KaiaMessage
from kaia.avatar import AvatarApi
from kaia.narrator import World

class KaiaMessageTranslator(Translator):
    def __init__(self,
                 inner_function,
                 kaia_api: KaiaGuiApi,
                 avatar_api: None|AvatarApi = None,
                 name_to_image: Optional[Callable[[str], str]] = None
                 ):
        self.kaia_api = kaia_api
        self.avatar_api = avatar_api
        self.name_to_image = name_to_image
        super().__init__(
            inner_function,
            None,
            self._incoming_utterance,
            None,
            self._outgoing_utterance,
            None
        )

    def _set_name_and_avatar(self, message: KaiaMessage, field: str):
        if self.avatar_api is not None:
            message.speaker = self.avatar_api.state_get().get(field, None)
            if message.speaker is not None and self.name_to_image is not None:
                message.avatar = self.name_to_image(message.speaker)


    def _incoming_utterance(self, input: TranslatorInputPackage):
        if isinstance(input.outer_input, Utterance):
            message = KaiaMessage(False, input.outer_input.to_str())
        elif isinstance(input.outer_input, str):
            message = KaiaMessage(False, input.outer_input)
        else:
            return input.outer_input

        if message is not None:
            self._set_name_and_avatar(message, World.user.field_name)
            self.kaia_api.add_message(message)

        return input.outer_input


    def _outgoing_utterance(self, output: Translator.OutputPackage):
        if isinstance(output.inner_output, KaiaMessage):
            message = output.inner_output
        elif isinstance(output.inner_output, Utterance):
            message = KaiaMessage(True, output.inner_output.to_str())
        elif isinstance(output.inner_output, str):
            message = KaiaMessage(True, output.inner_output)
        else:
            return output.inner_output

        self._set_name_and_avatar(message, World.character.field_name)
        return message


