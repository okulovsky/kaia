from .api import AvatarApi
from ..messaging import Stream, IMessage, Envelop
from .serialization import to_json, from_json, get_type_by_full_name, get_full_name_by_type

class AvatarStream(Stream):
    def __init__(self, api: AvatarApi, session: str = 'default'):
        self.api = api
        self.session = session

    def ready(self):
        self.api.wait()


    def put(self, message: IMessage):
        self.api.messaging.add(
            get_full_name_by_type(type(message)),
            self.session,
            to_json(message.envelop, type(message.envelop)),
            to_json(message, type(message))
        )

    def get(self, last_id: str|None = None, count: int|None = None) -> list[IMessage]:
        records = self.api.messaging.get(self.session, last_id, count)
        messages = []
        for record in records:
            _type = get_type_by_full_name(record['message_type'])
            message = from_json(record['payload'], _type)
            message._envelop = from_json(record['envelop'], Envelop)
            messages.append(message)
        return messages

