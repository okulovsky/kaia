from .common import State, message_handler, TextCommand, AvatarService, InternalTextCommand


class StateToUtterancesApplicationService(AvatarService):
    def __init__(self, state: State):
        self.state = state

    @message_handler
    def on_text_command(self, text: TextCommand) -> InternalTextCommand:
        return InternalTextCommand(
            text.text,
            text.user,
            text.language if text.language is not None else self.state.language,
            text.character if text.character is not None else self.state.character
        ).as_propagation_confirmation_to(text)


    def requires_brainbox(self):
        return False


