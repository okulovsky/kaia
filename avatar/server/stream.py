from .api import AvatarApi
from ..messaging import Stream, IMessage, Envelop
from .format import Format
from .naming import get_full_name_by_type, get_type_by_full_name

class AvatarStream(Stream):
    def __init__(self, api: AvatarApi, session: str = 'default'):
        self.api = api
        self.session = session

    def ready(self):
        self.api.wait()

    @staticmethod
    def to_json(message: IMessage, session: str):
        return dict(
            message_type = get_full_name_by_type(type(message)),
            session = session,
            envelop = Format.to_json(message.envelop, type(message.envelop)),
            payload = Format.to_json(message, type(message))
        )

    def put(self, message: IMessage):
        self.api.messaging.add(**AvatarStream.to_json(message, self.session))

    def get(self, last_id: str|None = None, count: int|None = None) -> list[IMessage]:
        records = self.api.messaging.get(self.session, last_id, count)
        messages = []
        for record in records:
            _type = get_type_by_full_name(record['message_type'])
            message = Format.from_json(record['payload'], _type)
            message._envelop = Format.from_json(record['envelop'], Envelop)
            messages.append(message)
        return messages

    def get_last_message_id(self) -> str|None:
        return self.api.messaging.last(self.session)

