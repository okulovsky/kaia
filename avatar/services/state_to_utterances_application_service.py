from .common import State, message_handler, UtteranceSequenceCommand, PlayableTextMessage, TextInfo, TextCommand, AvatarService


class StateToUtterancesApplicationService(AvatarService):
    def __init__(self, state: State):
        self.state = state

    @message_handler
    def on_utterance(self, text: UtteranceSequenceCommand) -> PlayableTextMessage[UtteranceSequenceCommand]:
        return PlayableTextMessage(
            text,
            TextInfo(
                self.state.character,
                self.state.language
            )
        )

    @message_handler
    def on_text(self, text: TextCommand) -> PlayableTextMessage[TextCommand]:
        return PlayableTextMessage(
            text,
            TextInfo(
                self.state.character,
                self.state.language
            )
        )

    def requires_brainbox(self):
        return False


