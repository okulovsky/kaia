from avatar.messaging import StreamClient, IMessage
from avatar.services import (
    SoundCommand, SoundInjectionCommand, SoundConfirmation, OpenMicCommand,
    WakeWordEvent, SoundEvent
)

class MessagesTranslator:
    def __init__(self, internal: StreamClient, external: StreamClient):
        self.internal = internal
        self.external = external
        self.id_to_old_message: dict[str, IMessage] = {}

    def iteration(self):
        external_messages = self.external.pull()
        for message in external_messages:
            if isinstance(message, (SoundCommand, SoundInjectionCommand, OpenMicCommand)):
                new_message = message.with_new_envelop()
                self.id_to_old_message[new_message.envelop.id] = message
                self.internal.put(new_message)

        internal_messages = self.internal.pull()
        for message in internal_messages:
            if isinstance(message, (WakeWordEvent, SoundEvent)):
                self.external.put(message.with_new_envelop().as_from_publisher('phonix'))
            if isinstance(message, SoundConfirmation):
                for confirmation_id in message.envelop.confirmation_for:
                    if confirmation_id in self.id_to_old_message:
                        original_message = self.id_to_old_message[confirmation_id]
                        new_message = (
                            message
                            .with_new_envelop()
                            .as_reply_to(original_message)
                            .as_confirmation_for(original_message)
                            .as_from_publisher('phonix')
                        )
                        self.external.put(new_message)
                        del self.id_to_old_message[confirmation_id]

