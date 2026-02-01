from avatar.messaging import IMessage
from avatar.daemon import TextEvent, UserWalkInService, TextCommand
from typing import Any, cast, Callable
from eaglesong import Translator, Listen
from grammatron import UtterancesSequence, Utterance
from ..assistant import KaiaContext, UserIdentification
from datetime import datetime



class StateTranslator(Translator):
    def __init__(self, inner, datetime_factory: Callable[[], datetime] = datetime.now):
        super().__init__(
            inner,
            input_function_translator=self._translate_input,
            output_function_translator=self._translate_output
        )
        self._candidate: UserIdentification|None = None
        self.datetime_factory = datetime_factory


    def _translate_input(self, input: Translator.InputPackage) -> Any:
        message = input.outer_input
        new_candidate = None
        if isinstance(message, TextEvent):
            new_candidate = UserIdentification(
                message.user,
                message.file_id,
                UserIdentification.Type.Voice,
                self.datetime_factory()
            )
        elif isinstance(message, UserWalkInService.Event):
            new_candidate = UserIdentification(
                message.user,
                message.file_id,
                UserIdentification.Type.Image,
                self.datetime_factory()
            )


        if new_candidate is not None:
            self._candidate = new_candidate
            kaia_context = cast(KaiaContext, input.inner_context)
            kaia_context.user = self._candidate.user

        if isinstance(message, TextEvent):
            return message.text
        else:
            return message

    def _translate_output(self, output: Translator.OutputPackage):
        message = output.inner_output
        context = cast(KaiaContext, output.inner_context)
        if isinstance(message, (str, Utterance, UtterancesSequence)):
            message = TextCommand(message)

        if isinstance(message, TextCommand):
            message.user = context.user
            message.language = context.language
            context.previous_identification = self._candidate

        if isinstance(message, Listen):
            self._candidate = None

        return message




