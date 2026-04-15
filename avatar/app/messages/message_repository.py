from .interface import IAvatarMessagingService
from ...messaging import IMessageRepository, IMessage, AvatarMessageSet
from .avatar_message import AvatarMessage
from foundation_kaia.marshalling import Serializer, TypeTools, JSON, ApiUtils
from dataclasses import dataclass

@dataclass
class GenericMessage(IMessage):
    content_type: str
    content: JSON


class AvatarMessageRepository(IMessageRepository):
    def __init__(self, service: IAvatarMessagingService):
        self.service = service

    @staticmethod
    def _serialize(session: str, message: IMessage) -> AvatarMessage:
        serializer = Serializer.parse(type(message))
        content = serializer.to_json(message, Serializer.Context())
        content_type = TypeTools.type_to_full_name(type(message))
        avatar_message = AvatarMessage(
            session,
            content_type,
            message.envelop,
            content
        )
        return avatar_message

    def put(self, session: str, message: IMessage):
        self.service.put(self._serialize(session, message))

    @staticmethod
    def _deserialize(result: AvatarMessageSet[AvatarMessage]) -> AvatarMessageSet[IMessage]:
        messages = []
        for m in result.messages:
            try:
                t = TypeTools.full_name_to_type(m.content_type)
            except Exception:
                t = None
            if t is None:
                new_message = GenericMessage(m.content_type, m.content)
            else:
                new_message = Serializer.parse(t).from_json(m.content, Serializer.Context())
            new_message._envelop = m.envelop
            messages.append(new_message)
        return AvatarMessageSet(result.missing_id, result.missing_session, messages)

    def get(self,
            session: str,
            last_id: str | None = None,
            timeout_in_seconds: float | None = None,
            max_messages: int | None = None,
            allowed_types: list[str] | None = None,
            ) -> AvatarMessageSet[IMessage]:
        return self._deserialize(self.service.get(session, last_id, timeout_in_seconds, max_messages, allowed_types))

    def tail(self,
             session: str,
             count: int|None = None,
             from_timestamp=None,
             ) -> AvatarMessageSet[IMessage]:
        return self._deserialize(self.service.tail(session, count, from_timestamp=from_timestamp))

    def wait_for_availability(self):
        from .service import AvatarMessagingService
        from .api import AvatarMessagingApi
        if isinstance(self.service, AvatarMessagingService):
            return
        elif isinstance(self.service, AvatarMessagingApi):
            address = self.service._base_url
            ApiUtils.wait_for_reply(address, 30, "Avatar Api")
            return
