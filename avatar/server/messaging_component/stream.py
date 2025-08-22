from ...messaging import Stream, IMessage

class AvatarStream(Stream):
    def __init__(self, api, session: str = 'default'):
        self.api = api
        self.session = session

    def ready(self):
        self.api.wait()

    def put(self, message: IMessage):
        self.api.messaging.add(self.session, message)

    def get_tail(self, count: int, types: tuple[type,...]|None = None) -> list[IMessage]:
        return self.api.messaging.tail(count, self.session, types)

    def get(self, last_id: str|None = None, count: int|None = None, types: tuple[type,...]|None = None) -> list[IMessage]:
        return self.api.messaging.get(self.session, last_id, count, types)

    def get_last_message_id(self) -> str|None:
        return self.api.messaging.last(self.session)

