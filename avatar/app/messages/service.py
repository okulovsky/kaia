from .avatar_message import AvatarMessage
from ...messaging.core import AvatarMessageSet, AvatarMessageSetElement, IMessage
from .interface import IAvatarMessagingService
from .queue import Queue
from datetime import datetime
from time import monotonic, sleep
from foundation_kaia.marshalling import TypeTools, Serializer
from pathlib import Path
from .stasher import Stasher

class AvatarMessagingService(IAvatarMessagingService):
    def __init__(self,
                 aliases: dict[str, type]|None = None,
                 ttl_in_seconds: int|None = 60*60,
                 starting_messages: dict[str,tuple[IMessage,...]]|None = None,
                 log_folder: Path|None = None,
                 ):
        self.ttl_in_seconds = ttl_in_seconds
        self.aliases = aliases
        self.queue: Queue = Queue(self.ttl_in_seconds)
        self.stasher = Stasher(log_folder) if log_folder is not None else None

        from .message_repository import AvatarMessageRepository
        if starting_messages is not None:
            for session, messages in starting_messages.items():
                for message in messages:
                    self.put(AvatarMessageRepository._serialize(session, message))

    def _ensure_full_type(self, t: str):
        if self.aliases is not None and t in self.aliases:
            return TypeTools.type_to_full_name(self.aliases[t])
        return t

    def put(self, message: AvatarMessage):
        message.content_type = self._ensure_full_type(message.content_type)
        message.envelop.timestamp = datetime.now()
        start = monotonic()
        self.queue.add(message)
        operation_time = monotonic() - start
        if self.stasher is not None:
            self.stasher.stash({
                'operation': 'put',
                'message': Serializer.parse(AvatarMessage).to_json(message, Serializer.Context()),
                'queue_size': self.queue.size,
                'operation_time': operation_time,
            })

    def get(self,
            session: str | None,
            last_id: str|None = None,
            timeout_in_seconds: float|None = None,
            max_messages: int|None = None,
            allowed_types: list[str]|None = None,
            client_name: str|None = None,
            ) -> AvatarMessageSet[AvatarMessage]:
        if not allowed_types:
            allowed_types = None

        if last_id is None:
            index = -1
            last_id_not_found = False
            operation_time = None
        else:
            start = monotonic()
            idx = self.queue.get_index(last_id)
            operation_time = monotonic() - start
            if idx is None:
                index = -1
                last_id_not_found = True
            else:
                index = idx
                last_id_not_found = False

        if self.stasher is not None:
            self.stasher.stash({
                'operation': 'get',
                'timestamp': str(datetime.now()),
                'session': session,
                'client_name': client_name,
                'last_id': last_id,
                'allowed_types': allowed_types,
                'queue_size': self.queue.size,
                'operation_time': operation_time,
            })

        start_index = max(index + 1, self.queue.first_index)

        begin_time = monotonic()
        while True:
            messages = self.queue.get_from(start_index)
            if session is not None:
                messages = [m for m in messages if m.session == session]
            if messages:
                if allowed_types is not None:
                    messages = [m for m in messages if any(m.content_type.endswith(t) for t in allowed_types)]
                if messages:
                    break
            if timeout_in_seconds is not None and monotonic() - begin_time > timeout_in_seconds:
                return AvatarMessageSet(last_id_not_found, [])
            sleep(0.01)

        if max_messages is not None:
            messages = messages[:max_messages]
        return AvatarMessageSet(last_id_not_found, [AvatarMessageSetElement(m.session, m) for m in messages])

    def tail(self,
             session: str,
             count: int|None = None,
             allowed_types: list[str]|None = None,
             from_timestamp=None,
             ) -> AvatarMessageSet[AvatarMessage]:

        start = monotonic()

        if not allowed_types:
            allowed_types = None

        if from_timestamp is not None:
            start = self.queue.find_index_from_timestamp(from_timestamp)
            messages = self.queue.get_from(start)
        else:
            messages = self.queue.get_from(self.queue.first_index)

        messages = [m for m in messages if m.session == session]

        if allowed_types is not None:
            messages = [m for m in messages if any(m.content_type.endswith(t) for t in allowed_types)]

        if count is not None and from_timestamp is None:
            messages = messages[-count:]

        if self.stasher is not None:
            self.stasher.stash({
                'operation': 'tail',
                'timestamp': str(datetime.now()),
                'session': session,
                'allowed_types': allowed_types,
                'queue_size': self.queue.size,
                'operation_time': monotonic() - start,
            })

        return AvatarMessageSet(True, [AvatarMessageSetElement(m.session, m) for m in messages])
