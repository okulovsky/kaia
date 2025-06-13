from typing import *
from eaglesong.core import Translator, TranslatorInputPackage
from eaglesong.templates import Utterance
from kaia.kaia.server import KaiaApi, Message
from avatar import AvatarApi, WorldFields

class KaiaMessageTranslator(Translator):
    def __init__(self,
                 inner_function,
                 kaia_api: KaiaApi,
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

    def _set_name_and_avatar(self, message: Message, field: str):
        if self.avatar_api is not None:
            message.sender = self.avatar_api.state_get().get(field, None)
            if message.sender is not None and self.name_to_image is not None:
                message.avatar = self.name_to_image(message.sender)


    def _incoming_utterance(self, input: TranslatorInputPackage):
        if isinstance(input.outer_input, Utterance):
            message = Message(Message.Type.FromUser, input.outer_input.to_str())
        elif isinstance(input.outer_input, str):
            message = Message(Message.Type.FromUser, input.outer_input)
        else:
            return input.outer_input

        if message is not None:
            self._set_name_and_avatar(message, WorldFields.user)
            self.kaia_api.add_message(message)

        return input.outer_input


    def _outgoing_utterance(self, output: Translator.OutputPackage):
        if isinstance(output.inner_output, Message):
            message = output.inner_output
        elif isinstance(output.inner_output, Utterance):
            message = Message(Message.Type.ToUser, output.inner_output.to_str())
        elif isinstance(output.inner_output, str):
            message = Message(Message.Type.ToUser, output.inner_output)
        else:
            return output.inner_output

        self._set_name_and_avatar(message, WorldFields.character)
        return message


